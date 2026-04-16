# Quick Start - Webhook + Splunk Evidence

This is the shortest supported path for the current setup.

## 1. Start the local receiver

```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
python3 start.py
```

The app listens on `127.0.0.1:8081`.

## 2. Start ngrok in another terminal

```bash
ngrok http 8081
```

Copy the public URL and use:

```text
https://<ngrok-host>/webhook/incident
```

## 3. Update ServiceNow

In the ServiceNow PDI:

- keep Business Rule `Incident AI Analyzer Webhook` enabled
- confirm it runs `after insert`
- set system property `x_servicenow_incident_analyzer.webhook_url` to the ngrok webhook URL

## 4. Create or insert an incident

For incidents that include identifiers such as `request_id`, `quote_number`, `application`, `service_name`, or `environment`, the agent will:

1. fetch the incident details
2. search Splunk for exact matches first
3. fall back to contextual or similar matching if needed
4. attach a `splunk_evidence_...txt` report
5. add an `[AI Evidence Attachment]` work note
6. post an `[AI Incident Analysis]` comment
7. reassign the ticket when confidence is high enough

## 5. Watch it live

```bash
tail -f logs/webhook.log
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/webhook/stats
```

## What success looks like

In ServiceNow you should see:

- one AI analysis comment
- one AI evidence work note
- one Splunk evidence attachment
- updated assignment group when confidence is high

In `logs/webhook.log` you should see:

- `success: True`
- `comment_posted: True`
- `reassigned: True`
- `evidence_attached: True`

## Useful files

- [`README.md`](README.md)
- [`docs/SPLUNK_EVIDENCE_FLOW.md`](docs/SPLUNK_EVIDENCE_FLOW.md)
- [`docs/WEBHOOK_IMPLEMENTATION_SUMMARY.md`](docs/WEBHOOK_IMPLEMENTATION_SUMMARY.md)
