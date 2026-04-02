"""LLM-based incident analyzer using LangChain and NVIDIA AI Endpoints."""

import json
import logging
from typing import Dict, Any, List
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage

from langchain_core.tools import tool
from src.mock_kb import MockKnowledgeBase
from src.logging import setup_llm_analysis_logging

logger = logging.getLogger(__name__)
llm_logger = setup_llm_analysis_logging()


class IncidentAnalyzer:
    """Analyzes incidents using LLM and determines recommendations."""

    def __init__(self, openai_api_key: str, team_mappings: Dict[str, str], nvidia_api_key: str = None):
        """
        Initialize the incident analyzer.

        Args:
            openai_api_key: Not used (kept for compatibility)
            team_mappings: Mapping of categories to assignment groups
            nvidia_api_key: NVIDIA API key for ChatNVIDIA
        """
        self.llm = ChatNVIDIA(
            model="openai/gpt-oss-120b",
            api_key=nvidia_api_key,
            temperature=1,
            top_p=1,
            max_completion_tokens=4096
        )
        self.kb = MockKnowledgeBase()
        self.team_mappings = team_mappings

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

    def analyze_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
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
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # If no JSON found, create structured response from text
                analysis = self._extract_analysis_from_text(response, incident)

            # Ensure required fields exist
            required_fields = ["category", "root_cause", "resolution_steps", "recommended_assignment_group", "confidence"]
            for field in required_fields:
                if field not in analysis:
                    if field == "recommended_assignment_group":
                        # Map category to assignment group
                        category = analysis.get("category", "Application")
                        analysis[field] = self.team_mappings.get(category, self.team_mappings.get("default", "General-Support"))
                    else:
                        analysis[field] = self._get_default_value(field)

            # Ensure resolution_steps is a list
            if isinstance(analysis.get("resolution_steps"), str):
                analysis["resolution_steps"] = [analysis["resolution_steps"]]

            # Handle assignment_group_category field from LLM
            if "assignment_group_category" in analysis:
                category = analysis["assignment_group_category"]
                analysis["recommended_assignment_group"] = self.team_mappings.get(category, self.team_mappings.get("default", "General-Support"))
                del analysis["assignment_group_category"]

            # Validate and map assignment group
            if analysis["recommended_assignment_group"] not in self.team_mappings.values():
                # Try to find best match
                category = analysis.get("category", "").lower()
                mapped_group = None
                for cat_key, group_val in self.team_mappings.items():
                    if category == cat_key.lower():
                        mapped_group = group_val
                        break

                if not mapped_group:
                    mapped_group = self.team_mappings.get("default", "General-Support")

                analysis["recommended_assignment_group"] = mapped_group

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
            "recommended_assignment_group": self.team_mappings.get(category, "General-Support"),
            "confidence": 50,
            "analysis_summary": text[:200]
        }

    def _create_default_analysis(self, incident: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        """Create default analysis when processing fails."""
        category = incident.get("category", "Application")
        return {
            "category": category,
            "root_cause": "Unable to determine - manual review required",
            "resolution_steps": ["Contact support team", "Review incident logs"],
            "recommended_assignment_group": self.team_mappings.get(category, "General-Support"),
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
            "recommended_assignment_group": "General-Support",
            "confidence": 50
        }
        return defaults.get(field, "")

    def format_analysis_comment(self, analysis: Dict[str, Any], similar_incidents: List[Dict[str, Any]]) -> str:
        """
        Format analysis into a readable comment for the incident ticket.

        Args:
            analysis: Analysis result dictionary
            similar_incidents: List of similar past incidents

        Returns:
            Formatted comment string
        """
        comment_parts = [
            "[AI Incident Analysis]",
            f"Category: {analysis.get('category', 'N/A')}",
            f"Confidence: {analysis.get('confidence', 0)}%",
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

        comment_parts.append("")
        comment_parts.append(f"Recommended Assignment Group: {analysis.get('recommended_assignment_group', 'N/A')}")

        return "\n".join(comment_parts)
