"""LLM-based incident analyzer using LangChain and NVIDIA AI Endpoints."""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from src.mock_kb import MockKnowledgeBase
from src.logging import setup_llm_analysis_logging

logger = logging.getLogger(__name__)
llm_logger = setup_llm_analysis_logging()


class IncidentAnalyzer:
    """Analyzes incidents using LLM and determines recommendations."""

    def __init__(
        self,
        openai_api_key: str,
        team_mappings: Dict[str, str],
        nvidia_api_key: str = None,
        llm: Optional[Any] = None,
    ):
        """
        Initialize the incident analyzer.

        Args:
            openai_api_key: Not used (kept for compatibility)
            team_mappings: Mapping of categories to assignment groups
            nvidia_api_key: NVIDIA API key for ChatNVIDIA
        """
        self.llm = llm or ChatNVIDIA(
            model="openai/gpt-oss-120b",
            api_key=nvidia_api_key,
            temperature=1,
            top_p=1,
            max_completion_tokens=4096
        )
        self.kb = MockKnowledgeBase()
        self.team_mappings = team_mappings

    def get_default_assignment_group(self) -> str:
        """Return the default assignment group for fallback/manual triage."""
        return self.team_mappings.get("default", "General-Support")

    def _map_category_to_assignment_group(self, category: str) -> str:
        """Map a category to an assignment group with case-insensitive fallback."""
        default_group = self.team_mappings.get("default", "General-Support")

        if not category:
            return default_group

        if category in self.team_mappings:
            return self.team_mappings[category]

        category_lower = str(category).strip().lower()
        for mapped_category, assignment_group in self.team_mappings.items():
            if mapped_category.lower() == category_lower:
                return assignment_group

        return default_group

    def _parse_number_words(self, value: str) -> Optional[int]:
        """Convert simple spelled-out numbers such as 'thirty' into integers."""
        cleaned = value.strip().lower().replace("-", " ")
        if not cleaned:
            return None

        cleaned = re.sub(r"\b(percent|percentage|confidence)\b", "", cleaned).strip()
        if not cleaned:
            return None

        units = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
        }
        tens = {
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "fifty": 50,
            "sixty": 60,
            "seventy": 70,
            "eighty": 80,
            "ninety": 90,
        }

        total = 0
        current = 0
        for part in cleaned.split():
            if part == "and":
                continue
            if part in units:
                current += units[part]
            elif part in tens:
                current += tens[part]
            elif part == "hundred":
                current = max(current, 1) * 100
            else:
                return None

        total += current
        if 0 <= total <= 100:
            return total
        return None

    def _normalize_confidence(self, confidence: Any) -> int:
        """Normalize confidence values to an integer between 0 and 100."""
        if confidence is None:
            return 0

        if isinstance(confidence, bool):
            return int(confidence)

        if isinstance(confidence, (int, float)):
            return max(0, min(100, int(round(confidence))))

        confidence_text = str(confidence).strip()
        if not confidence_text:
            return 0

        numeric_match = re.search(r"-?\d+(?:\.\d+)?", confidence_text)
        if numeric_match:
            return max(0, min(100, int(round(float(numeric_match.group())))))

        word_value = self._parse_number_words(confidence_text)
        if word_value is not None:
            return word_value

        return 0

    def _repair_common_json_issues(self, json_payload: str) -> str:
        """Repair small, common LLM JSON issues before parsing."""
        def replace_confidence(match: re.Match) -> str:
            normalized_confidence = self._normalize_confidence(match.group(2))
            return f"{match.group(1)}{normalized_confidence}"

        repaired_payload = re.sub(
            r'("confidence"\s*:\s*)([^,\}\n]+)',
            replace_confidence,
            json_payload,
            count=1,
        )
        repaired_payload = re.sub(r",(\s*[}\]])", r"\1", repaired_payload)
        return repaired_payload

    def _load_json_analysis(self, json_payload: str, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Load an LLM JSON payload, repairing small issues when possible."""
        try:
            return json.loads(json_payload)
        except json.JSONDecodeError:
            repaired_payload = self._repair_common_json_issues(json_payload)
            if repaired_payload != json_payload:
                try:
                    return json.loads(repaired_payload)
                except json.JSONDecodeError:
                    pass

        logger.warning("Falling back to text extraction for incident %s due to malformed LLM JSON", incident.get("number", "unknown"))
        return self._extract_analysis_from_text(json_payload, incident)

    def _search_kb(self, query: str) -> str:
        """Search knowledge base for similar incidents."""
        try:
            results = self.kb.find_similar_incidents(query, limit=3)
            if not results:
                return "No similar incidents found in knowledge base."

            formatted_results = []
            for incident in results:
                formatted_results.append(
                    f"- {incident['title']} ({incident['category']}): "
                    f"{incident['root_cause']}. "
                    f"Steps: {', '.join(incident['resolution_steps'][:2])}"
                )
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error searching KB: {str(e)}")
            return f"Error searching knowledge base: {str(e)}"

    def _search_similar_incidents(self, description: str, title: str = "") -> List[Dict[str, Any]]:
        """Search for similar incidents in KB."""
        try:
            return self.kb.find_similar_incidents(description, title, limit=3)
        except Exception as e:
            logger.error(f"Error searching similar incidents: {str(e)}")
            return []

    def _format_kb_context(self, incidents: List[Dict[str, Any]]) -> str:
        """Format KB incidents for LLM context."""
        if not incidents:
            return "No similar incidents found."
        
        lines = []
        for incident in incidents:
            lines.append(f"- Title: {incident['title']}")
            lines.append(f"  Category: {incident['category']}")
            lines.append(f"  Root Cause: {incident['root_cause']}")
            lines.append(f"  Steps: {', '.join(incident['resolution_steps'][:2])}")
        return "\n".join(lines)

    def analyze_incident(self, incident: Dict[str, Any], evidence_context: str = "") -> Dict[str, Any]:
        """
        Analyze an incident and return recommendations.

        Args:
            incident: Incident dictionary from ServiceNow

        Returns:
            Analysis result with category, root cause, assignment group, etc.
        """
        try:
            incident_id = incident.get("sys_id", "unknown")
            incident_num = incident.get("number", "unknown")
            title = incident.get("short_description", "")
            description = incident.get("description", "")

            logger.info(f"Analyzing incident {incident_num} ({incident_id})")

            # Get similar incidents from KB
            similar = self._search_similar_incidents(description, title)

            # Build analysis prompt
            analysis_prompt = f"""Analyze this ServiceNow incident and provide recommendations:

Incident Number: {incident_num}
Title: {title}
Description: {description}
Current Category: {incident.get('category', 'Not set')}
Priority: {incident.get('priority', 'Unknown')}

Similar Past Incidents from KB:
{self._format_kb_context(similar)}

Splunk Evidence Context:
{evidence_context or "No relevant Splunk evidence found."}

Please determine:
1. Most appropriate incident category
2. Likely root cause hypothesis
3. Key resolution steps (2-3 most important)
4. Which team should handle this based on category

Guidelines:
- Use these categories: {', '.join(self.kb.get_all_categories())}
- Be concise and practical
- Focus on actionable root causes
- Provide confidence score 0-100
- If the incident title/description are vague, placeholder-like, or missing concrete technical details, keep confidence very low and recommend manual review.
- Treat Splunk lookup failures as missing evidence only; do not assume the incident root cause is Splunk unless the incident text explicitly points there.

Respond in JSON format with fields: category, root_cause, resolution_steps (list), assignment_group_category, confidence (0-100)"""

            # Call LLM using invoke - GPT-OSS-120B returns reasoning in additional_kwargs
            response = self.llm.invoke([{"role": "user", "content": analysis_prompt}])
            
            # Extract reasoning and content from response
            response_text = response.content if response.content else str(response)
            reasoning_text = ""
            
            if hasattr(response, 'additional_kwargs'):
                if "reasoning_content" in response.additional_kwargs:
                    reasoning_text = response.additional_kwargs["reasoning_content"]
                elif "reasoning" in response.additional_kwargs:
                    reasoning_text = response.additional_kwargs["reasoning"]
            
            analysis = self._parse_analysis_response(response_text, incident, similar)
            
            # Create and log the analysis record
            class AnalysisRecord(logging.LogRecord):
                """Custom LogRecord that carries LLM analysis metadata."""
                pass
            
            record = AnalysisRecord(
                name="llm_analysis",
                level=logging.INFO,
                pathname=__file__,
                lineno=0,
                msg=f"LLM Analysis Complete for {incident_num}",
                args=(),
                exc_info=None
            )
            record.incident_number = incident_num
            record.llm_input = analysis_prompt
            record.llm_output = response_text
            record.reasoning = reasoning_text if reasoning_text else None
            record.confidence = analysis.get('confidence', 0)
            
            llm_logger.handle(record)

            logger.info(f"Analysis complete for {incident_num}. Category: {analysis.get('category')}, Confidence: {analysis.get('confidence')}%")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing incident {incident_num}: {str(e)}", exc_info=True)
            return self._create_default_analysis(incident, error=str(e))

    def _parse_analysis_response(self, response: str, incident: Dict[str, Any], similar_incidents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse LLM response and extract analysis data.

        Args:
            response: LLM response text
            incident: Original incident dictionary
            similar_incidents: Similar incidents from KB

        Returns:
            Parsed analysis dictionary
        """
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = self._load_json_analysis(json_match.group(), incident)
            else:
                # If no JSON found, create structured response from text
                analysis = self._extract_analysis_from_text(response, incident)

            if "confidence" in analysis:
                analysis["confidence"] = self._normalize_confidence(analysis.get("confidence"))

            # Ensure required fields exist
            required_fields = ["category", "root_cause", "resolution_steps", "recommended_assignment_group", "confidence"]
            for field in required_fields:
                if field not in analysis:
                    if field == "recommended_assignment_group":
                        # Map category to assignment group
                        category = analysis.get("category", "Application")
                        analysis[field] = self._map_category_to_assignment_group(category)
                    else:
                        analysis[field] = self._get_default_value(field)

            # Ensure resolution_steps is a list
            if isinstance(analysis.get("resolution_steps"), str):
                analysis["resolution_steps"] = [analysis["resolution_steps"]]

            # Handle assignment_group_category field from LLM
            if "assignment_group_category" in analysis:
                category = analysis["assignment_group_category"]
                analysis["recommended_assignment_group"] = self._map_category_to_assignment_group(category)
                del analysis["assignment_group_category"]

            # Validate and map assignment group
            if analysis["recommended_assignment_group"] not in self.team_mappings.values():
                # Try to find best match
                analysis["recommended_assignment_group"] = self._map_category_to_assignment_group(
                    analysis.get("category", "")
                )

            return analysis

        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return self._create_default_analysis(incident, error=str(e))

    def _extract_analysis_from_text(self, text: str, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Extract analysis from unstructured text response."""
        # Simple extraction - in production, could use NLP
        description = incident.get("description", "").lower()
        title = incident.get("short_description", "").lower()
        combined = f"{title} {description}"

        # Try to determine category from keywords
        category = "Application"  # default
        for kb_incident in self.kb.incidents:
            for keyword in kb_incident["keywords"]:
                if keyword in combined:
                    category = kb_incident["category"]
                    break

        return {
            "category": category,
            "root_cause": "To be determined from incident analysis",
            "resolution_steps": ["Review incident details", "Contact relevant team"],
            "recommended_assignment_group": self._map_category_to_assignment_group(category),
            "confidence": 50,
            "analysis_summary": text[:200]
        }

    def _create_default_analysis(self, incident: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        """Create default analysis when processing fails."""
        category = incident.get("category") or "Application"
        return {
            "category": category,
            "root_cause": "Unable to determine - manual review required",
            "resolution_steps": ["Contact support team", "Review incident logs"],
            "recommended_assignment_group": self._map_category_to_assignment_group(category),
            "confidence": 0,
            "analysis_summary": f"Error during analysis: {error}",
            "error": error
        }

    def _get_default_value(self, field: str) -> Any:
        """Get default value for analysis field."""
        defaults = {
            "category": "Application",
            "root_cause": "To be determined",
            "resolution_steps": [],
            "recommended_assignment_group": self.get_default_assignment_group(),
            "confidence": 50
        }
        return defaults.get(field, "")

    def build_manual_review_analysis(
        self,
        incident: Dict[str, Any],
        current_analysis: Optional[Dict[str, Any]] = None,
        evidence_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a safe low-confidence fallback when the ticket lacks real signal."""
        current_analysis = current_analysis or {}
        valid_categories = set(self.kb.get_all_categories())
        category = current_analysis.get("category")
        if category not in valid_categories:
            category = "Application"

        has_relevant_evidence = bool((evidence_summary or {}).get("match_count"))
        evidence_clause = "" if has_relevant_evidence else " and no relevant Splunk evidence was found"

        return {
            "category": category,
            "root_cause": (
                "Insufficient useful incident detail to determine a reliable root cause. "
                "The ticket content appears vague or placeholder-like"
                f"{evidence_clause}."
            ),
            "resolution_steps": [
                "Contact the requester for the exact error message, affected service/module, timestamp, and steps to reproduce.",
                "Capture concrete identifiers such as request ID, quote number, hostname, or username before rerunning log analysis.",
                "Keep the ticket in manual triage until actionable evidence is available.",
            ],
            "recommended_assignment_group": self.get_default_assignment_group(),
            "confidence": min(self._normalize_confidence(current_analysis.get("confidence", 0)), 20),
        }

    def format_analysis_comment(
        self,
        analysis: Dict[str, Any],
        similar_incidents: List[Dict[str, Any]],
        evidence_summary: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Format analysis into a readable comment for the incident ticket.

        Args:
            analysis: Analysis result dictionary
            similar_incidents: List of similar past incidents

        Returns:
            Formatted comment string
        """
        confidence = self._normalize_confidence(analysis.get("confidence", 0))
        comment_parts = [
            "[AI Incident Analysis]",
            f"Category: {analysis.get('category', 'N/A')}",
            f"Confidence: {confidence}%",
            "",
            "Root Cause Analysis:",
            f"  {analysis.get('root_cause', 'N/A')}",
            "",
            "Recommended Resolution Steps:",
        ]

        for i, step in enumerate(analysis.get('resolution_steps', []), 1):
            comment_parts.append(f"  {i}. {step}")

        if similar_incidents:
            comment_parts.append("")
            comment_parts.append("Similar Past Incidents:")
            for incident in similar_incidents[:3]:
                comment_parts.append(f"  - {incident.get('title', 'N/A')}")

        if evidence_summary:
            strategy = evidence_summary.get("search_strategy", "")
            strategy_label = strategy.replace("_", " ") if strategy else "n/a"
            comment_parts.append("")
            comment_parts.append("Splunk Evidence:")
            comment_parts.append(f"  Match Mode: {evidence_summary.get('search_mode', 'none')}")
            if evidence_summary.get("search_strategy"):
                comment_parts.append(f"  Match Strategy: {strategy_label}")
            comment_parts.append(f"  Matches Found: {evidence_summary.get('match_count', 0)}")
            if evidence_summary.get("top_event"):
                top_event = evidence_summary["top_event"]
                comment_parts.append(
                    "  Top Match: "
                    f"{top_event.get('application', 'N/A')} / "
                    f"{top_event.get('service_name', 'N/A')} / "
                    f"{top_event.get('error_message', 'N/A')}"
                )
            if evidence_summary.get("attachment_name"):
                comment_parts.append(f"  Evidence Attachment: {evidence_summary['attachment_name']}")

        if confidence < 60:
            comment_parts.append("")
            comment_parts.append("Manual Review Recommended:")
            comment_parts.append("  Low-confidence analysis due to limited or ambiguous incident detail. Verify with the requester before reassignment or closure.")

        comment_parts.append("")
        comment_parts.append(f"Recommended Assignment Group: {analysis.get('recommended_assignment_group', 'N/A')}")

        return "\n".join(comment_parts)

    def format_evidence_work_note(self, evidence_summary: Dict[str, Any]) -> str:
        """Format a concise work note describing attached Splunk evidence."""
        strategy = evidence_summary.get("search_strategy", "")
        strategy_label = strategy.replace("_", " ") if strategy else "n/a"
        lines = [
            "[AI Evidence Attachment]",
            f"Splunk Match Mode: {evidence_summary.get('search_mode', 'none')}",
            f"Splunk Match Strategy: {strategy_label}",
            f"Splunk Matches Found: {evidence_summary.get('match_count', 0)}",
        ]

        if evidence_summary.get("attachment_name"):
            lines.append(f"Attached Evidence File: {evidence_summary['attachment_name']}")

        if evidence_summary.get("top_event"):
            top_event = evidence_summary["top_event"]
            lines.append(
                "Top Match: "
                f"{top_event.get('application', 'N/A')} / "
                f"{top_event.get('service_name', 'N/A')} / "
                f"{top_event.get('error_message', 'N/A')}"
            )

        if evidence_summary.get("query"):
            lines.append("Splunk search query stored in attachment report.")

        return "\n".join(lines)
