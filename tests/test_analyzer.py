"""Tests for incident analyzer and processor."""

import unittest
from unittest.mock import Mock
from src.mock_kb import MockKnowledgeBase
from src.incident_analyzer import IncidentAnalyzer


class TestMockKnowledgeBase(unittest.TestCase):
    """Test cases for MockKnowledgeBase."""

    def setUp(self):
        """Set up test fixtures."""
        self.kb = MockKnowledgeBase()

    def test_kb_initialization(self):
        """Test KB initialization with sample incidents."""
        self.assertGreater(len(self.kb.incidents), 0)
        self.assertEqual(len(self.kb.incidents), 10)

    def test_find_similar_incidents(self):
        """Test finding similar incidents."""
        results = self.kb.find_similar_incidents("database connection timeout")
        self.assertGreater(len(results), 0)
        # Should find database-related incident
        self.assertEqual(results[0]["category"], "Database")

    def test_get_all_categories(self):
        """Test getting all categories."""
        categories = self.kb.get_all_categories()
        self.assertIn("Infrastructure", categories)
        self.assertIn("Database", categories)

    def test_get_incidents_by_category(self):
        """Test filtering incidents by category."""
        incidents = self.kb.get_incidents_by_category("Database")
        self.assertGreater(len(incidents), 0)
        for incident in incidents:
            self.assertEqual(incident["category"], "Database")


class TestIncidentAnalyzer(unittest.TestCase):
    """Test cases for IncidentAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.team_mappings = {
            "Infrastructure": "IT-Infrastructure-Team",
            "Database": "DBA-Team",
            "Networking": "Network-Operations",
            "Application": "Application-Support",
            "default": "General-Support"
        }
        self.analyzer = IncidentAnalyzer(
            openai_api_key="test_key",
            team_mappings=self.team_mappings,
            llm=Mock()
        )

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer.kb)
        self.assertIsNotNone(self.analyzer.team_mappings)
        self.assertEqual(self.analyzer.team_mappings["Database"], "DBA-Team")

    def test_format_analysis_comment(self):
        """Test formatting analysis into comment."""
        analysis = {
            "category": "Database",
            "root_cause": "Connection pool exhaustion",
            "resolution_steps": ["Check connections", "Restart service"],
            "recommended_assignment_group": "DBA-Team",
            "confidence": 85
        }
        similar = [{"title": "DB Connection Timeout"}]

        evidence = {
            "search_mode": "exact",
            "match_count": 2,
            "attachment_name": "splunk_evidence_INC0001.txt",
            "top_event": {
                "application": "CASUALTY",
                "service_name": "createSession",
                "error_message": "Timeout"
            }
        }

        comment = self.analyzer.format_analysis_comment(analysis, similar, evidence_summary=evidence)
        self.assertIn("Database", comment)
        self.assertIn("85%", comment)
        self.assertIn("DBA-Team", comment)
        self.assertIn("Splunk Evidence", comment)
        self.assertIn("splunk_evidence_INC0001.txt", comment)

    def test_format_analysis_comment_flags_manual_review_for_low_confidence(self):
        """Low-confidence analyses should still include a manual review note."""
        analysis = {
            "category": "Application",
            "root_cause": "Insufficient incident detail",
            "resolution_steps": ["Contact the requester"],
            "recommended_assignment_group": "Application-Support",
            "confidence": 45
        }

        comment = self.analyzer.format_analysis_comment(analysis, [])
        self.assertIn("Manual Review Recommended", comment)
        self.assertIn("Recommended Assignment Group: Application-Support", comment)

    def test_get_default_value(self):
        """Test getting default values."""
        default_cat = self.analyzer._get_default_value("category")
        self.assertEqual(default_cat, "Application")

        default_conf = self.analyzer._get_default_value("confidence")
        self.assertEqual(default_conf, 50)

    def test_format_evidence_work_note(self):
        """Test formatting an evidence work note."""
        note = self.analyzer.format_evidence_work_note({
            "search_mode": "similar",
            "match_count": 3,
            "attachment_name": "evidence.txt",
            "query": "search index=api_ui_logs",
            "top_event": {
                "application": "CASUALTY",
                "service_name": "createSession",
                "error_message": "Timeout"
            }
        })
        self.assertIn("AI Evidence Attachment", note)
        self.assertIn("evidence.txt", note)

    def test_parse_analysis_response_repairs_spelled_out_confidence(self):
        """Malformed JSON confidence values should be repaired when possible."""
        response = """```json
{
  "category": "Application",
  "root_cause": "Missing details from reporter",
  "resolution_steps": [
    "Contact the requester"
  ],
  "assignment_group_category": "Application",
  "confidence": thirty
}
```"""
        incident = {
            "number": "INC0001",
            "category": "inquiry",
            "short_description": "blah blah blah",
            "description": "sddds"
        }

        analysis = self.analyzer._parse_analysis_response(response, incident)
        self.assertEqual(analysis["category"], "Application")
        self.assertEqual(analysis["confidence"], 30)
        self.assertEqual(analysis["recommended_assignment_group"], "Application-Support")

    def test_build_manual_review_analysis_uses_default_group_and_low_confidence(self):
        """Placeholder incidents should fall back to a safe manual review analysis."""
        analysis = self.analyzer.build_manual_review_analysis(
            incident={
                "number": "INC0002",
                "short_description": "blah blah blah",
                "description": "blah blah blah",
            },
            current_analysis={
                "category": "Infrastructure",
                "recommended_assignment_group": "IT-Infrastructure-Team",
                "confidence": 68,
            },
            evidence_summary={"match_count": 0},
        )

        self.assertEqual(analysis["category"], "Infrastructure")
        self.assertEqual(analysis["recommended_assignment_group"], "General-Support")
        self.assertEqual(analysis["confidence"], 20)
        self.assertIn("Insufficient useful incident detail", analysis["root_cause"])


if __name__ == "__main__":
    unittest.main()
