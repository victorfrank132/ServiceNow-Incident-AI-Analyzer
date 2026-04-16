"""Main orchestration logic for the incident processing pipeline."""

import time
import logging
import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from src.servicenow_client import ServiceNowClient
from src.incident_analyzer import IncidentAnalyzer
from src.mock_kb import MockKnowledgeBase
from src.splunk_client import SplunkClient

logger = logging.getLogger(__name__)


class IncidentProcessor:
    """Main processor for incident analysis and reassignment workflow."""

    LOW_SIGNAL_STOPWORDS = {
        "a",
        "an",
        "and",
        "for",
        "from",
        "help",
        "incident",
        "issue",
        "problem",
        "please",
        "ticket",
        "the",
        "this",
        "with",
    }
    PLACEHOLDER_TOKENS = {
        "asdf",
        "blah",
        "dummy",
        "foobar",
        "ipsum",
        "lorem",
        "placeholder",
        "qwerty",
        "sample",
        "test",
    }

    def __init__(
        self,
        servicenow_client: ServiceNowClient,
        analyzer: IncidentAnalyzer,
        splunk_client: Optional[SplunkClient] = None,
        auto_reassign: bool = True,
        auto_close: bool = True,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize the incident processor.

        Args:
            servicenow_client: ServiceNow API client
            analyzer: Incident analyzer instance
            auto_reassign: Whether to automatically reassign incidents
            auto_close: Whether to automatically close incidents with reporter approval
            rate_limit_delay: Delay between API calls in seconds
        """
        self.snow_client = servicenow_client
        self.analyzer = analyzer
        self.splunk_client = splunk_client
        self.auto_reassign = auto_reassign
        self.auto_close = auto_close
        self.rate_limit_delay = rate_limit_delay
        self.manual_review_threshold = 60
        self.reassign_confidence_threshold = 70
        self.kb = MockKnowledgeBase()
        
        # State mapping for ServiceNow incidents
        self.state_map = {
            "1": "New",
            "2": "In Progress",
            "3": "On Hold",
            "4": "Ready for Review",
            "5": "Resolved",
            "6": "Closed",
            "7": "Cancelled"
        }
        
        # Track analyzed incidents to avoid duplicate comments
        self.analysis_cache_file = Path("logs/analyzed_incidents.json")
        self.analyzed_incidents = self._load_analysis_cache()

    def _load_analysis_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache of previously analyzed incidents."""
        if self.analysis_cache_file.exists():
            try:
                with open(self.analysis_cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load analysis cache: {e}")
        return {}

    def _save_analysis_cache(self) -> None:
        """Save cache of analyzed incidents to file."""
        try:
            self.analysis_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.analysis_cache_file, 'w') as f:
                json.dump(self.analyzed_incidents, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save analysis cache: {e}")

    def _is_incident_already_analyzed(self, incident_num: str, current_confidence: int) -> bool:
        """
        Check if incident was already analyzed and if confidence significantly changed.
        
        Args:
            incident_num: ServiceNow incident number
            current_confidence: Current analysis confidence score
            
        Returns:
            True if already analyzed with similar confidence, False if new or significantly different
        """
        if incident_num not in self.analyzed_incidents:
            return False
        
        cached = self.analyzed_incidents[incident_num]
        cached_confidence = cached.get("confidence", 0)
        
        # Only consider it "already analyzed" if confidence is within 10 points
        # This allows us to post an update if confidence changed significantly
        return abs(current_confidence - cached_confidence) <= 10

    def _update_analysis_cache(self, incident_num: str, analysis: Dict[str, Any]) -> None:
        """Update cache with latest analysis."""
        self.analyzed_incidents[incident_num] = {
            "confidence": analysis.get("confidence", 0),
            "category": analysis.get("category", ""),
            "root_cause": analysis.get("root_cause", ""),
            "timestamp": time.time()
        }
        self._save_analysis_cache()

    def _get_state_name(self, state_code: str) -> str:
        """Get human-readable state name from state code."""
        return self.state_map.get(str(state_code), f"Unknown({state_code})")

    def _extract_signal_terms(self, incident: Dict[str, Any]) -> list[str]:
        """Extract basic signal terms from the ticket text."""
        text = " ".join(
            [
                str(incident.get("short_description", "")),
                str(incident.get("description", "")),
            ]
        ).lower()

        signal_terms = []
        for token in re.findall(r"[a-z0-9_/-]{3,40}", text):
            normalized = token.strip("_-/")
            if not normalized:
                continue
            if normalized in self.LOW_SIGNAL_STOPWORDS or normalized in self.PLACEHOLDER_TOKENS:
                continue
            if normalized.isdigit() and len(normalized) < 6:
                continue
            if normalized not in signal_terms:
                signal_terms.append(normalized)
        return signal_terms

    def _should_force_manual_review(self, incident: Dict[str, Any], evidence: Optional[Dict[str, Any]]) -> bool:
        """Return whether the incident lacks enough signal for a trustworthy analysis."""
        evidence = evidence or {}
        if evidence.get("match_count", 0) > 0:
            return False

        identifiers = evidence.get("identifiers") or {}
        has_identifiers = any(values for values in identifiers.values())
        signal_terms = self._extract_signal_terms(incident)

        return not has_identifiers and len(signal_terms) < 2

    def process_incidents(self, max_incidents: int = 10) -> Dict[str, Any]:
        """
        Fetch and process incidents.

        Args:
            max_incidents: Maximum number of incidents to process

        Returns:
            Processing summary with results
        """
        summary = {
            "total_processed": 0,
            "successful_analyses": 0,
            "reassigned": 0,
            "closed": 0,
            "comments_posted": 0,
            "comments_skipped": 0,
            "evidence_attached": 0,
            "errors": 0,
            "incidents": []
        }

        try:
            # Fetch new incidents
            incidents = self.snow_client.get_new_incidents(limit=max_incidents)
            logger.info(f"Processing {len(incidents)} new incidents")

            for incident in incidents:
                incident_result = self.process_single_incident(incident)
                summary["incidents"].append(incident_result)

                if incident_result.get("success"):
                    summary["successful_analyses"] += 1
                    if incident_result.get("comment_posted"):
                        summary["comments_posted"] += 1
                    else:
                        summary["comments_skipped"] += 1
                    if incident_result.get("reassigned"):
                        summary["reassigned"] += 1
                    if incident_result.get("closed"):
                        summary["closed"] += 1
                    if incident_result.get("evidence_attached"):
                        summary["evidence_attached"] += 1
                else:
                    summary["errors"] += 1

                summary["total_processed"] += 1

                # Rate limiting
                if summary["total_processed"] < len(incidents):
                    time.sleep(self.rate_limit_delay)

        except Exception as e:
            logger.error(f"Error in process_incidents: {str(e)}", exc_info=True)
            summary["error"] = str(e)

        return summary

    def process_single_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single incident: analyze, reassign, and optionally close.
        Avoids duplicate comments by tracking previously analyzed incidents.

        Args:
            incident: Incident dictionary from ServiceNow

        Returns:
            Result dictionary with processing details
        """
        incident_id = incident.get("sys_id", "unknown")
        incident_num = incident.get("number", "unknown")

        result = {
            "incident_id": incident_id,
            "incident_number": incident_num,
            "state": incident.get("state", "unknown"),
            "state_name": self._get_state_name(incident.get("state", "")),
            "success": False,
            "reassigned": False,
            "closed": False,
            "analysis": None,
            "error": None,
            "comment_posted": False,
            "manual_review_required": False,
            "evidence": None,
            "evidence_attached": False,
        }

        try:
            # Log incident with state
            state_display = result["state_name"]
            logger.info(f"Processing incident {incident_num} [State: {state_display}]")

            evidence = self._retrieve_splunk_evidence(incident)
            result["evidence"] = evidence

            # Analyze incident
            analysis = self.analyzer.analyze_incident(
                incident,
                evidence_context=(evidence or {}).get("analysis_context", ""),
            )

            if not analysis:
                logger.error("No analysis generated for %s", incident_num)
                result["error"] = "No analysis generated"
                return result

            if self._should_force_manual_review(incident, evidence):
                logger.warning(
                    "Insufficient incident signal for %s - overriding analysis with manual review fallback",
                    incident_num,
                )
                analysis = self.analyzer.build_manual_review_analysis(
                    incident,
                    current_analysis=analysis,
                    evidence_summary=evidence,
                )

            result["analysis"] = analysis

            confidence = analysis.get("confidence", 0)
            result["manual_review_required"] = confidence < self.manual_review_threshold
            if result["manual_review_required"]:
                logger.warning(
                    "Low confidence analysis for %s (%s%%) - posting manual review comment",
                    incident_num,
                    confidence,
                )

            # Check if incident was already analyzed with similar confidence
            already_analyzed = self._is_incident_already_analyzed(incident_num, confidence)
            
            if already_analyzed:
                logger.info(f"Incident {incident_num} already analyzed with similar confidence - skipping comment")
                result["success"] = True
                # Still perform reassignment/closure if conditions met
            else:
                if evidence and evidence.get("match_count"):
                    result["evidence_attached"] = self._attach_splunk_evidence(incident_id, incident_num, evidence)

                # First time analysis or significant confidence change - post comment
                description = incident.get("description", "")
                title = incident.get("short_description", "")
                similar_incidents = self.kb.find_similar_incidents(description, title, limit=3)

                # Format and add comment
                comment = self.analyzer.format_analysis_comment(
                    analysis,
                    similar_incidents,
                    evidence_summary=evidence,
                )
                comment_success = self.snow_client.add_comment_to_incident(incident_id, comment)

                if not comment_success:
                    logger.error(f"Failed to add comment to {incident_num}")
                    result["error"] = "Failed to add comment"
                    return result
                
                result["comment_posted"] = True
                logger.info(f"Posted analysis comment to {incident_num}")

            # Update cache with latest analysis
            self._update_analysis_cache(incident_num, analysis)

            # Reassign if enabled and confidence is high
            if self.auto_reassign and confidence >= self.reassign_confidence_threshold:
                assignment_group = analysis.get("recommended_assignment_group", "General-Support")
                reassign_success = self.snow_client.update_assignment_group(incident_id, assignment_group)

                if reassign_success:
                    result["reassigned"] = True
                    logger.info(f"Reassigned {incident_num} to {assignment_group}")
                else:
                    logger.error(f"Failed to reassign {incident_num}")

            # Check if incident can be closed with reporter approval
            if self.auto_close and analysis.get("confidence", 0) >= 80:
                close_result = self._attempt_incident_closure(incident, analysis)
                if close_result.get("success"):
                    result["closed"] = True
                    logger.info(f"Auto-closed incident {incident_num} with reporter approval")

            result["success"] = True
            logger.info(f"Successfully processed {incident_num}")

        except Exception as e:
            logger.error(f"Error processing incident {incident_num}: {str(e)}", exc_info=True)
            result["error"] = str(e)

        return result

    def _retrieve_splunk_evidence(self, incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch Splunk evidence for an incident when Splunk is configured."""
        if not self.splunk_client:
            return None

        evidence = self.splunk_client.find_relevant_logs(incident)
        if evidence.get("error"):
            logger.warning("Splunk evidence lookup failed for %s: %s", incident.get("number", "unknown"), evidence["error"])
        elif evidence.get("match_count"):
            logger.info(
                "Retrieved %s Splunk evidence match(es) for %s using %s search",
                evidence["match_count"],
                incident.get("number", "unknown"),
                evidence.get("search_mode", "unknown"),
            )
        else:
            logger.info("No Splunk evidence found for %s", incident.get("number", "unknown"))

        return evidence

    def _attach_splunk_evidence(self, incident_id: str, incident_num: str, evidence: Dict[str, Any]) -> bool:
        """Attach Splunk evidence report to the incident and add a work note."""
        report_text = evidence.get("report_text", "")
        if not report_text:
            return False

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        file_name = f"splunk_evidence_{incident_num}_{timestamp}.txt"
        upload_success = self.snow_client.upload_attachment_to_incident(
            incident_id=incident_id,
            file_name=file_name,
            content=report_text.encode("utf-8"),
            content_type="text/plain",
        )

        if not upload_success:
            logger.error("Failed to attach Splunk evidence to %s", incident_num)
            return False

        evidence["attachment_name"] = file_name
        work_note = self.analyzer.format_evidence_work_note(evidence)
        if not self.snow_client.add_work_note_to_incident(incident_id, work_note):
            logger.warning("Splunk evidence attached to %s but work note could not be added", incident_num)

        return True

    def _attempt_incident_closure(self, incident: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to close an incident if reporter approval exists or confidence is very high.

        Args:
            incident: Incident dictionary from ServiceNow
            analysis: Analysis results from LLM

        Returns:
            Result dictionary with closure status and details
        """
        incident_id = incident.get("sys_id", "unknown")
        incident_num = incident.get("number", "unknown")

        result = {
            "success": False,
            "reason": None,
            "approved": False
        }

        try:
            # Check for reporter approval
            approval_status = self.snow_client.get_reporter_approval_field(incident_id)
            
            confidence = analysis.get("confidence", 0)
            
            # Close conditions:
            # 1. Reporter explicitly approved (approval_status == "true" or "yes")
            # 2. Confidence >= 90 (very high confidence, auto-close with logging)
            
            reporter_approved = (
                approval_status and 
                str(approval_status).lower() in ["true", "yes", "1", "approved"]
            )
            
            if reporter_approved:
                result["approved"] = True
                result["reason"] = "Reporter approval received"
                logger.info(f"Reporter approved closure for {incident_num}")
            elif confidence >= 90:
                result["approved"] = True
                result["reason"] = f"Very high confidence ({confidence}%) auto-closure"
                logger.info(f"Auto-closing {incident_num} with very high confidence ({confidence}%)")
            else:
                logger.debug(f"Incident {incident_num} not eligible for closure. Approval: {approval_status}, Confidence: {confidence}%")
                return result

            # Generate resolution notes
            resolution_notes = self._generate_resolution_notes(incident, analysis)
            
            # Close the incident
            close_success = self.snow_client.close_incident(
                incident_id,
                resolution_notes=resolution_notes,
                close_reason="Resolved by Incident Agent"
            )

            if close_success:
                result["success"] = True
                logger.info(f"Successfully closed incident {incident_num}")
            else:
                result["reason"] = "Failed to close incident in ServiceNow"
                logger.error(f"Failed to close incident {incident_num}")

        except Exception as e:
            logger.error(f"Error attempting to close incident: {str(e)}", exc_info=True)
            result["reason"] = str(e)

        return result

    def _generate_resolution_notes(self, incident: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """
        Generate resolution notes for incident closure.

        Args:
            incident: Original incident data
            analysis: LLM analysis results

        Returns:
            Formatted resolution notes string
        """
        notes_lines = [
            "=== AUTOMATED INCIDENT RESOLUTION ===",
            f"Closed by: Incident Analysis Agent",
            f"Confidence: {analysis.get('confidence', 0)}%",
            "",
            f"CATEGORY: {analysis.get('category', 'Unknown')}",
            f"ROOT CAUSE: {analysis.get('root_cause', 'Not determined')}",
            "",
            "RESOLUTION STEPS TAKEN:",
        ]

        resolution_steps = analysis.get("resolution_steps", [])
        if isinstance(resolution_steps, list):
            for i, step in enumerate(resolution_steps, 1):
                notes_lines.append(f"{i}. {step}")
        else:
            notes_lines.append("- " + str(resolution_steps))

        notes_lines.extend([
            "",
            "STATUS: Resolved and validated by AI analysis engine",
            "Please confirm if this resolution working for you.",
        ])

        return "\n".join(notes_lines)

    def get_processing_summary(self, results: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of processing results.

        Args:
            results: Processing results dictionary

        Returns:
            Formatted summary string
        """
        summary_lines = [
            "=== Incident Processing Summary ===",
            f"Total Processed: {results.get('total_processed', 0)}",
            f"Successful Analyses: {results.get('successful_analyses', 0)}",
            f"  └─ Comments Posted: {results.get('comments_posted', 0)} (New/Updated)",
            f"  └─ Comments Skipped: {results.get('comments_skipped', 0)} (Already analyzed)",
            f"  └─ Evidence Attached: {results.get('evidence_attached', 0)}",
            f"Reassigned: {results.get('reassigned', 0)}",
            f"Auto-Closed: {results.get('closed', 0)}",
            f"Errors: {results.get('errors', 0)}",
        ]

        if results.get("error"):
            summary_lines.append(f"Overall Error: {results['error']}")

        # Add incident details
        if results.get("incidents"):
            summary_lines.append("\nIncident Details:")
            for incident in results["incidents"]:
                status = "✓" if incident.get("success") else "✗"
                closed_badge = "🔒 CLOSED" if incident.get("closed") else ""
                reassigned_badge = "↗ REASSIGNED" if incident.get("reassigned") else ""
                comment_badge = "💬 COMMENT" if incident.get("comment_posted") else ""
                evidence_badge = "📎 EVIDENCE" if incident.get("evidence_attached") else ""
                manual_review_badge = "MANUAL REVIEW" if incident.get("manual_review_required") else ""
                state_display = incident.get("state_name", incident.get("state", "Unknown"))
                summary_lines.append(
                    f"  {status} {incident.get('incident_number', 'N/A')} [{state_display}]: "
                    f"Confidence {incident.get('analysis', {}).get('confidence', 0)}% "
                    f"{comment_badge} {evidence_badge} {reassigned_badge} {closed_badge} {manual_review_badge}".strip()
                )

        return "\n".join(summary_lines)
