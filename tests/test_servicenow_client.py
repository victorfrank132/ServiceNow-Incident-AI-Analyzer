"""Tests for ServiceNow client wrapper."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.servicenow_client import ServiceNowClient


class TestServiceNowClient(unittest.TestCase):
    """Test cases for ServiceNowClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = ServiceNowClient(
            instance_url="https://dev12345.service-now.com",
            client_id="test_client",
            client_secret="test_secret"
        )

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.instance_url, "https://dev12345.service-now.com")
        self.assertEqual(self.client.client_id, "test_client")
        self.assertIn("/api/now/v2", self.client.api_url)

    def test_get_headers(self):
        """Test header generation."""
        headers = self.client._get_headers()
        self.assertIn("Content-Type", headers)
        self.assertEqual(headers["Content-Type"], "application/json")

    @patch("src.servicenow_client.requests.Session.get")
    def test_get_new_incidents_success(self, mock_get):
        """Test successful incident retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "123",
                    "number": "INC0001",
                    "short_description": "Test incident",
                    "state": "1"
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test
        incidents = self.client.get_new_incidents()
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["number"], "INC0001")

    @patch("src.servicenow_client.requests.Session.get")
    def test_get_new_incidents_api_error(self, mock_get):
        """Test incident retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        incidents = self.client.get_new_incidents()
        self.assertEqual(len(incidents), 0)

    @patch("src.servicenow_client.requests.Session.patch")
    def test_add_comment_success(self, mock_patch):
        """Test adding comment to incident."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        result = self.client.add_comment_to_incident("123", "Test comment")
        self.assertTrue(result)

    @patch("src.servicenow_client.requests.Session.patch")
    def test_add_comment_failure(self, mock_patch):
        """Test adding comment failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_patch.return_value = mock_response

        result = self.client.add_comment_to_incident("123", "Test comment")
        self.assertFalse(result)

    def test_get_category_options(self):
        """Test getting category options."""
        categories = self.client.get_category_options()
        self.assertIn("Infrastructure", categories)
        self.assertIn("Database", categories)


if __name__ == "__main__":
    unittest.main()
