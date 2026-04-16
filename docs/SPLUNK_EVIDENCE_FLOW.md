# Splunk Evidence Flow

## Overview

The webhook processor now enriches new ServiceNow incidents with Splunk evidence before posting the AI analysis back to the ticket.

## End-to-End Flow

```text
ServiceNow incident inserted
    ->
Business Rule: Incident AI Analyzer Webhook
    ->
System property: x_servicenow_incident_analyzer.webhook_url
    ->
ngrok tunnel
    ->
src/webhook_receiver.py
    ->
src/incident_processor.py
    ->
src/splunk_client.py exact search
    ->
fallback exact contextual search
    ->
fallback similar keyword search
    ->
upload evidence report attachment
    ->
add evidence work note
    ->
run AI analysis with evidence context
    ->
post AI comment
    ->
reassign incident
```

## Match Strategy Order

### 1. Exact identifier match

Highest-priority fields:

- `request_id`
- `quote_number`

Current strategy label:

- `request_or_quote`

This is the preferred path because it gives the cleanest and most reliable evidence set.

### 2. Exact contextual match

Used when strong identifiers are missing:

- `application`
- `service_name`
- `environment`

Current strategy label:

- `service_context`

### 3. Similar keyword match

Fallback when exact identifiers are unavailable:

- extracted keywords from short description and description
- scored against structured fields and raw event text

Current strategy label:

- `keyword_similarity`

## Evidence Artifacts Written Back to ServiceNow

For incidents with evidence matches, the processor creates:

1. A text attachment named like `splunk_evidence_INC0010072_20260406T070148Z.txt`
2. A work note beginning with `[AI Evidence Attachment]`
3. An analysis comment beginning with `[AI Incident Analysis]`

## Files Involved

- [`../src/splunk_client.py`](../src/splunk_client.py)
- [`../src/incident_processor.py`](../src/incident_processor.py)
- [`../src/servicenow_client.py`](../src/servicenow_client.py)
- [`../src/incident_analyzer.py`](../src/incident_analyzer.py)
- [`../src/webhook_receiver.py`](../src/webhook_receiver.py)

## Configuration

Environment variables:

```env
SPLUNK_ENABLED=true
SPLUNK_BASE_URL=https://your-stack.splunkcloud.com
SPLUNK_USERNAME=your_splunk_username
SPLUNK_PASSWORD=your_splunk_password
SPLUNK_INDEXES=api_ui_logs
SPLUNK_APP=search
SPLUNK_OWNER=nobody
SPLUNK_LOOKBACK=-30d
SPLUNK_MAX_RESULTS=5
```

YAML defaults:

```yaml
splunk:
  enabled: true
  indexes: ["api_ui_logs"]
  app: "search"
  owner: "nobody"
  lookback: "-30d"
  max_results: 5
```

## Verified Behavior

Verified on April 5, 2026 Pacific Time / April 6, 2026 UTC:

- `INC0010072` matched Splunk using exact `request_or_quote`
- 1 exact log event was found
- the evidence attachment was uploaded to ServiceNow
- the evidence work note was added
- the AI analysis comment was added
- the incident was reassigned to `Application Development`

## Operational Notes

- The supported local listener is `python3 start.py` on `127.0.0.1:8081`.
- Manual ngrok is the recommended tunnel path for this workspace.
- The older pyngrok bootstrap path may fail on this machine because of local SSL certificate verification during ngrok download.
