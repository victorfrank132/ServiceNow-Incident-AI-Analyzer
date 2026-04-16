"""Tests for incident processor behavior."""

import unittest
from unittest.mock import Mock, patch

from src.incident_processor import IncidentProcessor


class TestIncidentProcessor(unittest.TestCase):
    """Test cases for IncidentProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.snow_client = Mock()
        self.analyzer = Mock()

        load_cache_patcher = patch.object(IncidentProcessor, "_load_analysis_cache", return_value={})
        self.addCleanup(load_cache_patcher.stop)
        load_cache_patcher.start()

        self.processor = IncidentProcessor(
            servicenow_client=self.snow_client,
            analyzer=self.analyzer,
            splunk_client=None,
            auto_reassign=True,
            auto_close=False,
        )
        self.processor._save_analysis_cache = Mock()
        self.processor.kb.find_similar_incidents = Mock(return_value=[])

        self.snow_client.add_comment_to_incident.return_value = True
        self.snow_client.update_assignment_group.return_value = True

    def test_low_confidence_analysis_posts_comment_without_reassignment(self):
        """Low-confidence analysis should still be written back for human review."""
        incident = {
            "sys_id": "123",
            "number": "INC0001",
            "state": "1",
            "short_description": "blah blah blah",
            "description": "no useful details",
        }
        analysis = {
            "category": "Infrastructure",
            "root_cause": "Insufficient detail to determine a precise cause",
            "resolution_steps": ["Contact the requester for exact symptoms"],
            "recommended_assignment_group": "Incident Management",
            "confidence": 45,
        }

        self.analyzer.analyze_incident.return_value = analysis
        self.analyzer.format_analysis_comment.return_value = "[AI Incident Analysis]"

        result = self.processor.process_single_incident(incident)

        self.assertTrue(result["success"])
        self.assertTrue(result["comment_posted"])
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["error"])
        self.snow_client.add_comment_to_incident.assert_called_once_with("123", "[AI Incident Analysis]")
        self.snow_client.update_assignment_group.assert_not_called()

    def test_missing_analysis_still_returns_error(self):
        """Completely missing analysis should still fail cleanly."""
        incident = {
            "sys_id": "123",
            "number": "INC0002",
            "state": "1",
        }

        self.analyzer.analyze_incident.return_value = None

        result = self.processor.process_single_incident(incident)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No analysis generated")
        self.snow_client.add_comment_to_incident.assert_not_called()

    def test_placeholder_incident_overrides_high_confidence_guess(self):
        """Placeholder tickets should be downgraded to safe manual review output."""
        incident = {
            "sys_id": "123",
            "number": "INC0003",
            "state": "1",
            "short_description": "blah blah blah",
            "description": "blah blah blah",
        }
        evidence = {
            "analysis_context": "Splunk evidence was unavailable because the lookup failed.",
            "error": "Expecting value",
            "events": [],
            "identifiers": {
                "applications": [],
                "environments": [],
                "quote_numbers": [],
                "request_ids": [],
                "service_names": [],
            },
            "match_count": 0,
            "match_terms": [],
            "query": None,
            "report_text": "",
            "search_mode": "none",
            "search_strategy": None,
            "top_event": None,
        }
        raw_analysis = {
            "category": "Infrastructure",
            "root_cause": "Splunk integration issue",
            "resolution_steps": ["Check Splunk"],
            "recommended_assignment_group": "Incident Management",
            "confidence": 68,
        }
        manual_review_analysis = {
            "category": "Infrastructure",
            "root_cause": "Insufficient useful incident detail to determine a reliable root cause.",
            "resolution_steps": ["Contact the requester"],
            "recommended_assignment_group": "Incident Management",
            "confidence": 20,
        }

        self.processor._retrieve_splunk_evidence = Mock(return_value=evidence)
        self.analyzer.analyze_incident.return_value = raw_analysis
        self.analyzer.build_manual_review_analysis.return_value = manual_review_analysis
        self.analyzer.format_analysis_comment.return_value = "[AI Incident Analysis]"

        result = self.processor.process_single_incident(incident)

        self.assertTrue(result["success"])
        self.assertTrue(result["manual_review_required"])
        self.assertEqual(result["analysis"]["confidence"], 20)
        self.assertEqual(result["analysis"]["root_cause"], manual_review_analysis["root_cause"])
        self.analyzer.build_manual_review_analysis.assert_called_once()
        self.snow_client.update_assignment_group.assert_not_called()


if __name__ == "__main__":
    unittest.main()
