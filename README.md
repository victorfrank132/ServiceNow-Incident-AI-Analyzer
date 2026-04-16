# ServiceNow Incident AI Analyzer

Production-ready incident automation for ServiceNow that can process incidents in real time, retrieve matching Splunk evidence, attach the evidence back to the ticket, post AI analysis, and reassign the incident to the right team.

## Features

- Real-time webhook processing from ServiceNow insert events
- Exact-match Splunk evidence retrieval using `request_id` and `quote_number`
- Contextual fallback matching using application, service, and environment
- Similar-match fallback when exact identifiers are missing
- Evidence attachment upload to ServiceNow plus evidence work notes
- AI analysis comments with root cause, steps, and assignment recommendation
- Auto-reassignment when confidence is high enough
- Deduplication cache to avoid repeated comment spam
- Optional polling mode via `main.py`

## Supported Runtime Flow

The current production path is:

1. ServiceNow Business Rule `Incident AI Analyzer Webhook` runs `after insert`.
2. The Business Rule reads the system property `x_servicenow_incident_analyzer.webhook_url`.
3. ServiceNow POSTs the incident payload to the local webhook through ngrok.
4. [`src/webhook_receiver.py`](src/webhook_receiver.py) fetches the full incident from ServiceNow.
5. [`src/incident_processor.py`](src/incident_processor.py) retrieves Splunk evidence, uploads a text report attachment, writes an evidence work note, generates AI analysis, posts the analysis comment, and reassigns the incident.

Recommended local runtime:

- Start the receiver with `python3 start.py`
- Run `ngrok http 8081` in a second terminal
- Point the ServiceNow property at `https://<your-ngrok-host>/webhook/incident`

`main_webhook.py` is now a legacy path. Manual ngrok plus `start.py` is the recommended setup.

## Quick Start

### 1. Install and configure

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env
```

Fill in `config/.env` with:

```env
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
NVIDIA_API_KEY=your_nvidia_api_key

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

### 2. Start the local webhook receiver

```bash
source .venv/bin/activate
python3 start.py
```

The receiver listens on `127.0.0.1:8081`.

### 3. Start ngrok

```bash
ngrok http 8081
```

Copy the public `https://...` URL and append `/webhook/incident`.

### 4. Point ServiceNow to the webhook

In the ServiceNow PDI:

- Keep the Business Rule `Incident AI Analyzer Webhook` active
- Confirm it runs `after` insert
- Set the property `x_servicenow_incident_analyzer.webhook_url` to:

```text
https://<your-ngrok-host>/webhook/incident
```

### 5. Verify locally

```bash
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/webhook/stats
tail -f logs/webhook.log
```

## Splunk Evidence Retrieval

The evidence workflow is identifier-first:

1. Exact `request_id` and `quote_number` search
2. Exact contextual search using `application`, `service_name`, and `environment`
3. Similar-match keyword search when exact identifiers are missing

For positive matches, the processor:

- writes a `splunk_evidence_<incident>_<timestamp>.txt` attachment
- adds an `[AI Evidence Attachment]` work note
- includes the evidence summary in the AI incident analysis comment

## Configuration

Primary app settings live in [`config/config.yaml`](config/config.yaml).

Current Splunk block:

```yaml
splunk:
  enabled: true
  indexes: ["api_ui_logs"]
  app: "search"
  owner: "nobody"
  lookback: "-30d"
  max_results: 5
```

## Technical Flow

```text
ServiceNow Incident Insert
    ->
Business Rule: Incident AI Analyzer Webhook
    ->
System Property: x_servicenow_incident_analyzer.webhook_url
    ->
ngrok tunnel
    ->
start.py / src.webhook_receiver Flask app on 127.0.0.1:8081
    ->
Fetch full incident from ServiceNow
    ->
Splunk exact match (request_id / quote_number)
    ->
Splunk contextual fallback or similar fallback if needed
    ->
Attach evidence report + add evidence work note
    ->
LLM analysis with evidence context
    ->
Post AI analysis comment
    ->
Update assignment group
```

## Core Files

- [`start.py`](start.py): supported local webhook entry point
- [`main.py`](main.py): polling mode entry point
- [`src/webhook_receiver.py`](src/webhook_receiver.py): Flask webhook endpoints
- [`src/incident_processor.py`](src/incident_processor.py): orchestration for evidence, analysis, and writeback
- [`src/splunk_client.py`](src/splunk_client.py): Splunk Cloud login and search helpers
- [`src/servicenow_client.py`](src/servicenow_client.py): ServiceNow incident, comment, work note, and attachment API wrapper
- [`docs/SPLUNK_EVIDENCE_FLOW.md`](docs/SPLUNK_EVIDENCE_FLOW.md): detailed webhook + Splunk evidence flow
- [`QUICKSTART_UNIFIED.md`](QUICKSTART_UNIFIED.md): concise local startup guide

## Testing

```bash
./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python -m compileall src tests
```

## Notes

- The webhook receiver is healthy at `http://127.0.0.1:8081/health`.
- Manual ngrok is recommended on this machine because the older pyngrok auto-download path has hit a local SSL certificate verification issue.
