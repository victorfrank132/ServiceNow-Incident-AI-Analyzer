"""Tests for Splunk evidence retrieval helpers."""

import unittest

from src.splunk_client import SplunkClient


class TestSplunkClient(unittest.TestCase):
    """Test cases for SplunkClient helper logic."""

    def setUp(self):
        """Create a lightweight client for query-builder tests."""
        self.client = SplunkClient(
            base_url="https://example.splunkcloud.com",
            username="user",
            password="pass",
            indexes=["api_ui_logs"],
        )

    def test_extract_identifiers(self):
        """Identifiers should be extracted from incident text."""
        incident = {
            "short_description": "CASUALTY createSession failed for quote 35052368",
            "description": "request_id _169027998189 in PROD returned service timeout",
        }

        identifiers = self.client.extract_identifiers(incident)

        self.assertIn("_169027998189", identifiers["request_ids"])
        self.assertIn("35052368", identifiers["quote_numbers"])
        self.assertIn("CASUALTY", identifiers["applications"])
        self.assertIn("createSession", identifiers["service_names"])
        self.assertIn("PROD", identifiers["environments"])

    def test_build_exact_search(self):
        """Exact search should prioritize request/quote identifiers."""
        query = self.client.build_exact_search({
            "request_ids": ["_169027998189"],
            "quote_numbers": ["35052368"],
            "applications": ["CASUALTY"],
            "service_names": ["createSession"],
            "environments": ["PROD"],
        })

        self.assertIn('request_id="_169027998189"', query)
        self.assertIn('quote_number="35052368"', query)
        self.assertIn("index=api_ui_logs", query)
        self.assertNotIn('application="CASUALTY"', query)
        self.assertNotIn('service_name="createSession"', query)

    def test_build_exact_searches_adds_contextual_fallback(self):
        """Contextual fallback should use AND semantics across app/service/env."""
        exact_searches = self.client.build_exact_searches({
            "request_ids": [],
            "quote_numbers": [],
            "applications": ["CASUALTY"],
            "service_names": ["createSession"],
            "environments": ["PROD"],
        })

        self.assertEqual(exact_searches[0]["strategy"], "service_context")
        self.assertIn('application="CASUALTY"', exact_searches[0]["query"])
        self.assertIn('service_name="createSession"', exact_searches[0]["query"])
        self.assertIn('environment="PROD"', exact_searches[0]["query"])
        self.assertIn(" AND ", exact_searches[0]["query"])

    def test_build_similar_search(self):
        """Similar search should include the computed score expression."""
        query = self.client.build_similar_search(["timeout", "createSession", "CASUALTY"])

        self.assertIn("match_score", query)
        self.assertIn('"timeout"', query)
        self.assertIn('"createSession"', query)

    def test_normalize_event_flattens_duplicate_multivalue_fields(self):
        """Duplicate multivalue fields should collapse to a readable scalar."""
        event = self.client.normalize_event({
            "application": ["CASUALTY", "CASUALTY"],
            "service_name": ["createSession", "createSession"],
            "error_message": ["Timeout", "Timeout"],
        })

        self.assertEqual(event["application"], "CASUALTY")
        self.assertEqual(event["service_name"], "createSession")
        self.assertEqual(event["error_message"], "Timeout")

    def test_build_analysis_context(self):
        """Analysis context should summarize the top evidence rows."""
        context = self.client.build_analysis_context({
            "search_mode": "exact",
            "search_strategy": "request_or_quote",
            "match_count": 1,
            "events": [
                {
                    "_time": "2026-04-02 11:42:08.000 UTC",
                    "application": "CASUALTY",
                    "service_name": "createSession",
                    "environment": "PROD",
                    "quote_number": "35052368",
                    "request_id": "_169027998189",
                    "error_message": "Timeout",
                }
            ],
        })

        self.assertIn("Splunk Evidence Search Mode: exact", context)
        self.assertIn("Splunk Match Strategy: request or quote", context)
        self.assertIn("CASUALTY", context)


if __name__ == "__main__":
    unittest.main()
