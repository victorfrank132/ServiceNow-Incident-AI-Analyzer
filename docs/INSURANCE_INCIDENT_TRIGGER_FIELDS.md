# Insurance Incident Trigger Fields

Use the CSV in this folder for manual incident creation in ServiceNow.

## Minimum fields for this repo to process an incident well

- `short_description`
- `description`

Those are the two most important fields because the analyzer, keyword extraction, and fallback matching all read them.

## Recommended fields for better routing and triage

- `category`
- `priority`
- `urgency`
- `impact`
- `assignment_group`

These align with the fields used by the local `create_incident(...)` helper and the incident fetch logic.

## Strongly recommended identifiers for Splunk evidence matching

Put these either in dedicated ServiceNow fields, if your form has them, or directly inside the description text:

- `request_id`
- `quote_number`
- `application`
- `service_name`
- `environment`

This project prefers exact Splunk matches on `request_id` and `quote_number`, then falls back to `application`, `service_name`, and `environment`.

## Trigger requirements by flow type

### Webhook flow

For the real-time webhook flow to fire successfully:

- the ServiceNow Business Rule `Incident AI Analyzer Webhook` must be enabled
- it must run `after insert`
- system property `x_servicenow_incident_analyzer.webhook_url` must point to your ngrok URL plus `/webhook/incident`
- the local receiver must be running with `python start.py`
- the incident must actually be newly inserted

For manual UI creation, ServiceNow will generate the incident `number` automatically, which is enough for the webhook receiver to fetch full incident details.

### Polling flow

If you are testing through `main.py` instead of the webhook path, keep the incident in:

- `New` (`state=1`), or
- `In Progress` (`state=2`)

The polling client only fetches incidents in those states.

## ServiceNow form note

Some ServiceNow instances make fields like `caller` or `caller_id` mandatory on the form. That is instance-specific UI configuration, not a requirement from this repo. If your form blocks save without a caller, fill it in with any valid test caller in your instance.
