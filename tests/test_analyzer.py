"""Tests for incident analyzer and processor."""

import unittest
from unittest.mock import Mock, patch, MagicMock
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
        
        # Mock OpenAI API to avoid actual API calls
        with patch("src.incident_analyzer.OpenAI"):
            self.analyzer = IncidentAnalyzer(
                openai_api_key="test_key",
                team_mappings=self.team_mappings
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

        comment = self.analyzer.format_analysis_comment(analysis, similar)
        self.assertIn("Database", comment)
        self.assertIn("85%", comment)
        self.assertIn("DBA-Team", comment)

    def test_get_default_value(self):
        """Test getting default values."""
        default_cat = self.analyzer._get_default_value("category")
        self.assertEqual(default_cat, "Application")

        default_conf = self.analyzer._get_default_value("confidence")
        self.assertEqual(default_conf, 50)


if __name__ == "__main__":
    unittest.main()
