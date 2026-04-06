"""Splunk client for retrieving incident evidence from Splunk Cloud."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SplunkClient:
    """Retrieve incident evidence from Splunk Cloud via the Splunk Web proxy."""

    DEFAULT_INDEXES = ["api_ui_logs"]
    KNOWN_APPLICATIONS = {
        "CASUALTY",
        "DENTAL",
        "DISABILITY",
        "GL",
        "LIFE",
        "PROP",
        "VISION",
        "WC",
    }
    KNOWN_ENVIRONMENTS = {"DEV", "PROD", "QA", "STAGING", "UAT"}
    STOPWORDS = {
        "a",
        "an",
        "and",
        "api",
        "application",
        "app",
        "case",
        "check",
        "contact",
        "customer",
        "data",
        "error",
        "failure",
        "for",
        "from",
        "incident",
        "info",
        "issue",
        "log",
        "logs",
        "not",
        "number",
        "please",
        "prod",
        "problem",
        "request",
        "service",
        "servicenow",
        "staging",
        "support",
        "team",
        "test",
        "the",
        "this",
        "ticket",
        "trace",
        "webhook",
        "with",
    }

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        indexes: Optional[List[str]] = None,
        app: str = "search",
        owner: str = "nobody",
        lookback: str = "-30d",
        max_results: int = 5,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.indexes = indexes or self.DEFAULT_INDEXES
        self.app = app
        self.owner = owner
        self.lookback = lookback
        self.max_results = max_results
        self.session = session or requests.Session()
        self._csrf_token: Optional[str] = None
        self._logged_in = False

    def is_configured(self) -> bool:
        """Return whether the client has enough config to run searches."""
        return all([self.base_url, self.username, self.password])

    def _login(self) -> None:
        """Authenticate against the Splunk Web login flow and keep the session cookies."""
        if self._logged_in:
            return

        login_url = f"{self.base_url}/en-US/account/login"
        response = self.session.get(login_url, timeout=30)
        response.raise_for_status()

        cval_match = re.search(r'"cval":(\d+)', response.text)
        if not cval_match:
            raise RuntimeError("Unable to parse Splunk login cval token")

        cval = cval_match.group(1)
        login_response = self.session.post(
            login_url,
            data={
                "username": self.username,
                "password": self.password,
                "cval": cval,
            },
            timeout=30,
        )
        login_response.raise_for_status()

        self._csrf_token = cval
        for cookie_name, cookie_value in self.session.cookies.items():
            if cookie_name.startswith("splunkweb_csrf_token_"):
                self._csrf_token = cookie_value
                break

        self._logged_in = True

    def _proxy_url(self, path: str) -> str:
        return f"{self.base_url}/en-US/splunkd/__raw{path}"

    def _headers(self) -> Dict[str, str]:
        self._login()
        return {
            "Accept": "application/json",
            "Referer": f"{self.base_url}/en-US/app/{self.app}/search",
            "X-Requested-With": "XMLHttpRequest",
            "X-Splunk-Form-Key": self._csrf_token or "",
        }

    def list_indexes(self) -> List[str]:
        """Return indexes accessible to the configured user."""
        response = self.session.get(
            self._proxy_url(f"/servicesNS/{self.owner}/{self.app}/data/indexes"),
            headers=self._headers(),
            params={"count": 100, "output_mode": "json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return [entry["name"] for entry in payload.get("entry", [])]

    def run_search(self, search_query: str) -> List[Dict[str, Any]]:
        """Execute a Splunk export search and return row dictionaries."""
        response = self.session.post(
            self._proxy_url(f"/servicesNS/{self.owner}/{self.app}/search/jobs/export"),
            headers=self._headers(),
            data={
                "search": search_query,
                "output_mode": "json_rows",
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return self.normalize_search_results(payload)

    def find_relevant_logs(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Find exact or similar log evidence for an incident."""
        result = {
            "analysis_context": "",
            "error": None,
            "events": [],
            "identifiers": self.extract_identifiers(incident),
            "match_count": 0,
            "match_terms": [],
            "query": None,
            "report_text": "",
            "search_mode": "none",
            "search_strategy": None,
            "top_event": None,
        }

        if not self.is_configured():
            return result

        try:
            for exact_search in self.build_exact_searches(result["identifiers"]):
                exact_events = self.run_search(exact_search["query"])
                if exact_events:
                    result["events"] = exact_events
                    result["query"] = exact_search["query"]
                    result["search_mode"] = "exact"
                    result["search_strategy"] = exact_search["strategy"]
                    break

            if not result["events"]:
                result["match_terms"] = self.extract_match_terms(incident, result["identifiers"])
                similar_query = self.build_similar_search(result["match_terms"])
                if similar_query:
                    similar_events = self.run_search(similar_query)
                    if similar_events:
                        result["events"] = similar_events
                        result["query"] = similar_query
                        result["search_mode"] = "similar"
                        result["search_strategy"] = "keyword_similarity"

            result["match_count"] = len(result["events"])
            result["top_event"] = result["events"][0] if result["events"] else None
            result["analysis_context"] = self.build_analysis_context(result)
            result["report_text"] = self.build_report_text(incident, result)
            return result
        except Exception as exc:
            logger.warning("Splunk evidence retrieval failed: %s", exc)
            result["error"] = str(exc)
            result["analysis_context"] = f"Splunk evidence lookup failed: {exc}"
            result["report_text"] = self.build_report_text(incident, result)
            return result

    def extract_identifiers(self, incident: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract exact-match identifiers from incident fields and free text."""
        application_values = [
            str(value).strip().upper()
            for value in [
                incident.get("application", ""),
                incident.get("u_application", ""),
            ]
            if str(value).strip()
        ]
        environment_values = [
            str(value).strip().upper()
            for value in [
                incident.get("environment", ""),
                incident.get("u_environment", ""),
            ]
            if str(value).strip()
        ]
        service_values = [
            str(value).strip()
            for value in [
                incident.get("service_name", ""),
                incident.get("u_service_name", ""),
            ]
            if str(value).strip()
        ]

        text = " ".join(
            str(value)
            for value in [
                incident.get("short_description", ""),
                incident.get("description", ""),
                incident.get("request_id", ""),
                incident.get("u_request_id", ""),
                incident.get("quote_number", ""),
                incident.get("u_quote_number", ""),
                incident.get("application", ""),
                incident.get("u_application", ""),
                incident.get("service_name", ""),
                incident.get("u_service_name", ""),
                incident.get("environment", ""),
                incident.get("u_environment", ""),
            ]
            if value
        )

        request_ids = sorted(set(re.findall(r"\b_[0-9]{6,18}\b", text)))
        quote_numbers = sorted(set(re.findall(r"\b\d{8}\b", text)))

        service_names = sorted(
            set(service_values).union(
                {
                    token
                    for token in re.findall(r"\b[A-Za-z]+(?:[A-Z][a-z0-9]+)+\b", text)
                    if len(token) >= 6 and not re.fullmatch(r"INC\d+", token, re.IGNORECASE)
                }
            )
        )

        application_tokens = sorted(
            set(application_values).union(
                {
                    token.upper()
                    for token in re.findall(r"\b[A-Za-z]{2,20}\b", text)
                    if token.upper() in self.KNOWN_APPLICATIONS
                }
            )
        )
        environments = sorted(
            set(environment_values).union(
                {
                    token.upper()
                    for token in re.findall(r"\b[A-Za-z]{3,10}\b", text)
                    if token.upper() in self.KNOWN_ENVIRONMENTS
                }
            )
        )

        return {
            "applications": application_tokens,
            "environments": environments,
            "quote_numbers": quote_numbers,
            "request_ids": request_ids,
            "service_names": service_names,
        }

    def extract_match_terms(self, incident: Dict[str, Any], identifiers: Dict[str, List[str]]) -> List[str]:
        """Extract similarity-search terms from the incident body."""
        text = " ".join(
            [
                str(incident.get("short_description", "")),
                str(incident.get("description", "")),
            ]
        )

        tokens = []
        for token in re.findall(r"[A-Za-z0-9_/-]{4,40}", text):
            normalized = token.strip("_-/")
            lowered = normalized.lower()
            if not normalized or lowered in self.STOPWORDS:
                continue
            if lowered.isdigit() and len(lowered) < 6:
                continue
            tokens.append(normalized)

        match_terms = []
        for bucket in [
            identifiers.get("request_ids", []),
            identifiers.get("quote_numbers", []),
            identifiers.get("applications", []),
            identifiers.get("service_names", []),
            identifiers.get("environments", []),
        ]:
            match_terms.extend(bucket)

        for token in tokens:
            if token not in match_terms:
                match_terms.append(token)

        return match_terms[:8]

    def build_exact_search(self, identifiers: Dict[str, List[str]]) -> Optional[str]:
        """Return the highest-priority exact-match search query."""
        exact_searches = self.build_exact_searches(identifiers)
        if not exact_searches:
            return None
        return exact_searches[0]["query"]

    def build_exact_searches(self, identifiers: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Build prioritized exact-match searches from extracted identifiers."""
        searches: List[Dict[str, str]] = []

        strongest_filters: List[str] = []
        strongest_clauses: List[str] = []
        for request_id in identifiers.get("request_ids", []):
            escaped = self.escape_value(request_id)
            strongest_filters.append(f'"{escaped}"')
            strongest_clauses.append(f'request_id="{escaped}"')
        for quote_number in identifiers.get("quote_numbers", []):
            escaped = self.escape_value(quote_number)
            strongest_filters.append(f'"{escaped}"')
            strongest_clauses.append(f'quote_number="{escaped}"')

        if strongest_clauses:
            searches.append(
                {
                    "strategy": "request_or_quote",
                    "query": self._build_exact_query(
                        strongest_filters,
                        strongest_clauses,
                        group_operator="OR",
                        search_operator="OR",
                    ),
                }
            )

        contextual_fields = [
            ("application", identifiers.get("applications", [])),
            ("service_name", identifiers.get("service_names", [])),
            ("environment", identifiers.get("environments", [])),
        ]
        contextual_fields = [(field, values) for field, values in contextual_fields if values]

        if contextual_fields:
            contextual_filters = [self._build_prefilter_group(values) for _, values in contextual_fields]
            contextual_clauses = [self._build_where_group(field, values) for field, values in contextual_fields]
            searches.append(
                {
                    "strategy": "service_context",
                    "query": self._build_exact_query(
                        contextual_filters,
                        contextual_clauses,
                        group_operator="AND",
                        search_operator="AND",
                    ),
                }
            )

        return searches

    def build_similar_search(self, match_terms: List[str]) -> Optional[str]:
        """Build a similarity search based on incident text."""
        safe_terms = [term for term in match_terms if term]
        if not safe_terms:
            return None

        pre_filters = " OR ".join(f'"{self.escape_value(term)}"' for term in safe_terms)
        score_terms = []
        for term in safe_terms:
            lowered = self.escape_like(term.lower())
            score_terms.append(f'if(like(match_blob, "%{lowered}%"), 1, 0)')

        scope = self.build_scope()
        return (
            f"search {scope} earliest={self.lookback} ({pre_filters}) "
            "| spath "
            '| eval match_blob=lower(coalesce(request_id, "") . " " . coalesce(quote_number, "") . " " '
            '. coalesce(application, "") . " " . coalesce(service_name, "") . " " '
            '. coalesce(environment, "") . " " . coalesce(level, "") . " " '
            '. coalesce(error_message, "") . " " . coalesce(_raw, "")) '
            f"| eval match_score={' + '.join(score_terms)} "
            "| where match_score > 0 "
            "| sort - match_score - _time "
            '| eval match_mode="similar" '
            "| table _time index sourcetype source host quote_number request_id application "
            f"service_name environment level error_message match_score _raw | head {self.max_results}"
        )

    def build_scope(self) -> str:
        """Build the search scope across the configured indexes."""
        index_filters = [f"index={self.escape_value(index_name)}" for index_name in self.indexes]
        if len(index_filters) == 1:
            return index_filters[0]
        return f"({' OR '.join(index_filters)})"

    def build_analysis_context(self, evidence: Dict[str, Any]) -> str:
        """Create a concise context block for the analysis prompt."""
        if evidence.get("error"):
            return f"Splunk evidence lookup failed: {evidence['error']}"

        if not evidence.get("events"):
            return "No relevant Splunk evidence found."

        lines = [
            f"Splunk Evidence Search Mode: {evidence.get('search_mode', 'unknown')}",
            f"Splunk Matches Found: {evidence.get('match_count', 0)}",
        ]
        if evidence.get("search_strategy"):
            lines.append(f"Splunk Match Strategy: {self.humanize_strategy(evidence['search_strategy'])}")

        for index, event in enumerate(evidence["events"][:3], 1):
            lines.append(
                f"{index}. {event.get('_time', 'N/A')} | app={event.get('application', 'N/A')} "
                f"| service={event.get('service_name', 'N/A')} | env={event.get('environment', 'N/A')} "
                f"| quote={event.get('quote_number', 'N/A')} | request_id={event.get('request_id', 'N/A')} "
                f"| error={event.get('error_message', 'N/A')}"
            )

        return "\n".join(lines)

    def build_report_text(self, incident: Dict[str, Any], evidence: Dict[str, Any]) -> str:
        """Build an attachment-friendly evidence report."""
        lines = [
            "Splunk Evidence Report",
            "=" * 80,
            f"Incident Number: {incident.get('number', 'N/A')}",
            f"Incident Title: {incident.get('short_description', 'N/A')}",
            f"Search Mode: {evidence.get('search_mode', 'none')}",
            f"Match Strategy: {self.humanize_strategy(evidence.get('search_strategy'))}",
            f"Match Count: {evidence.get('match_count', 0)}",
            f"Indexes: {', '.join(self.indexes)}",
            f"Lookback: {self.lookback}",
            "",
            "Identifiers:",
            json.dumps(evidence.get("identifiers", {}), indent=2),
            "",
            "Search Terms:",
            ", ".join(evidence.get("match_terms", [])) or "None",
            "",
            "Query:",
            evidence.get("query") or "No query executed",
            "",
        ]

        if evidence.get("error"):
            lines.extend(
                [
                    "Error:",
                    evidence["error"],
                ]
            )
            return "\n".join(lines)

        if not evidence.get("events"):
            lines.append("No matching events found.")
            return "\n".join(lines)

        lines.append("Matched Events:")
        for index, event in enumerate(evidence["events"], 1):
            lines.extend(
                [
                    "",
                    f"Event #{index}",
                    "-" * 80,
                    f"Time: {event.get('_time', 'N/A')}",
                    f"Index: {event.get('index', 'N/A')}",
                    f"Sourcetype: {event.get('sourcetype', 'N/A')}",
                    f"Source: {event.get('source', 'N/A')}",
                    f"Host: {event.get('host', 'N/A')}",
                    f"Application: {event.get('application', 'N/A')}",
                    f"Service: {event.get('service_name', 'N/A')}",
                    f"Environment: {event.get('environment', 'N/A')}",
                    f"Level: {event.get('level', 'N/A')}",
                    f"Quote Number: {event.get('quote_number', 'N/A')}",
                    f"Request ID: {event.get('request_id', 'N/A')}",
                    f"Error Message: {event.get('error_message', 'N/A')}",
                    f"Match Score: {event.get('match_score', 'N/A')}",
                    "Raw:",
                    str(event.get("_raw", "")),
                ]
            )

        return "\n".join(lines)

    def _build_exact_query(
        self,
        pre_filters: List[str],
        where_clauses: List[str],
        group_operator: str,
        search_operator: str,
    ) -> str:
        """Assemble a complete exact-match Splunk query."""
        scope = self.build_scope()
        return (
            f"search {scope} earliest={self.lookback} ({f' {search_operator} '.join(pre_filters)}) "
            "| spath "
            f"| where {f' {group_operator} '.join(where_clauses)} "
            '| eval match_mode="exact" '
            "| table _time index sourcetype source host quote_number request_id application "
            f"service_name environment level error_message _raw | head {self.max_results}"
        )

    def _build_prefilter_group(self, values: List[str]) -> str:
        """Build a grouped pre-filter expression from string values."""
        escaped_values = [f'"{self.escape_value(value)}"' for value in values]
        if len(escaped_values) == 1:
            return escaped_values[0]
        return f"({' OR '.join(escaped_values)})"

    def _build_where_group(self, field_name: str, values: List[str]) -> str:
        """Build a grouped where-clause expression for a field."""
        clauses = [f'{field_name}="{self.escape_value(value)}"' for value in values]
        if len(clauses) == 1:
            return clauses[0]
        return f"({' OR '.join(clauses)})"

    def normalize_search_results(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Splunk json_rows payloads into normalized row dictionaries."""
        fields = payload.get("fields", [])
        rows = payload.get("rows", [])
        return [self.normalize_event(dict(zip(fields, row))) for row in rows]

    def normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize multi-value Splunk fields into readable scalars."""
        return {key: self.normalize_value(value) for key, value in event.items()}

    def normalize_value(self, value: Any) -> Any:
        """Flatten duplicated multivalue fields while preserving unique content."""
        if isinstance(value, list):
            normalized_items = []
            for item in value:
                normalized_item = self.normalize_value(item)
                if normalized_item in ("", None):
                    continue
                if normalized_item not in normalized_items:
                    normalized_items.append(normalized_item)

            if not normalized_items:
                return ""
            if len(normalized_items) == 1:
                return normalized_items[0]
            return ", ".join(str(item) for item in normalized_items)

        return value

    @staticmethod
    def humanize_strategy(strategy: Optional[str]) -> str:
        """Return a readable label for an internal search strategy name."""
        if not strategy:
            return "N/A"
        return strategy.replace("_", " ")

    @staticmethod
    def escape_value(value: str) -> str:
        """Escape double quotes and backslashes for Splunk string literals."""
        return str(value).replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def escape_like(value: str) -> str:
        """Escape LIKE wildcards for eval-based matching."""
        return SplunkClient.escape_value(value).replace("%", "\\%").replace("_", "\\_")


def build_splunk_client_from_env(config: Optional[Dict[str, Any]] = None) -> Optional[SplunkClient]:
    """Build a Splunk client from env/config, or return None when disabled."""
    config = config or {}
    enabled = str(os.getenv("SPLUNK_ENABLED", config.get("enabled", "true"))).lower() not in {"0", "false", "no"}
    base_url = os.getenv("SPLUNK_BASE_URL", config.get("base_url", ""))
    username = os.getenv("SPLUNK_USERNAME", config.get("username", ""))
    password = os.getenv("SPLUNK_PASSWORD", config.get("password", ""))

    if not enabled or not all([base_url, username, password]):
        return None

    raw_indexes = os.getenv("SPLUNK_INDEXES")
    if raw_indexes:
        indexes = [value.strip() for value in raw_indexes.split(",") if value.strip()]
    else:
        indexes = config.get("indexes") or SplunkClient.DEFAULT_INDEXES

    return SplunkClient(
        base_url=base_url,
        username=username,
        password=password,
        indexes=indexes,
        app=os.getenv("SPLUNK_APP", config.get("app", "search")),
        owner=os.getenv("SPLUNK_OWNER", config.get("owner", "nobody")),
        lookback=os.getenv("SPLUNK_LOOKBACK", config.get("lookback", "-30d")),
        max_results=int(os.getenv("SPLUNK_MAX_RESULTS", config.get("max_results", 5))),
    )
