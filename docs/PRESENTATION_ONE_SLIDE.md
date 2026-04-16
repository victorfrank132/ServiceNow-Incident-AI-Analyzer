# One-Slide Executive Summary

## Slide Title

ServiceNow Incident AI Analyzer

## Slide Subtitle

Real-time incident enrichment, AI-assisted triage, and guarded automation back into ServiceNow

## Slide Layout

Use a single-slide left-to-right process with 8 boxes.

Top:
- Title on the left
- Subtitle under title
- Small value statement on the right: Faster triage, better routing, fewer manual hops

Middle:
- 8 connected process boxes from left to right
- Use color grouping by stage

Bottom:
- Short legend
- 3 outcome metrics placeholders

## Recommended Box Copy

### 1. Incident Created
ServiceNow incident is inserted and becomes the starting event.

Tools:
ServiceNow Incident Table

### 2. Business Rule Trigger
After-insert rule reads the webhook URL from a system property and sends the event.

Tools:
ServiceNow Business Rule
System Property

### 3. Local Webhook Intake
The local Flask receiver accepts the webhook through ngrok.

Tools:
ngrok
Python
Flask

### 4. Incident Detail Fetch
The app fetches the full incident record to avoid relying on a minimal webhook payload.

Tools:
ServiceNow REST API
requests
ServiceNowClient

### 5. Splunk Evidence Search
The processor searches Splunk using request ID, quote number, app, service, and fallback matching.

Tools:
Splunk REST API
SplunkClient

### 6. AI Analysis
The LLM combines incident details, KB context, and evidence to suggest category, root cause, steps, and routing.

Tools:
Mock KB
LangChain
ChatNVIDIA
NVIDIA AI Endpoints
openai/gpt-oss-120b

### 7. Guardrails
Low-signal tickets are forced to manual review, low-confidence outputs stay non-destructive, and duplicate comments are suppressed.

Tools:
Confidence thresholds
Manual review fallback
analyzed_incidents.json

### 8. ServiceNow Write-Back
The app posts AI comments, evidence notes, attachments, and updates assignment groups when confidence is strong enough.

Tools:
Comments API
Work Notes API
Attachment API
Assignment Group update

## Outcome Strip

Add 3 small KPI boxes under the flow:

- Faster first-pass triage
- Better assignment-group recommendations
- Reduced analyst effort for repeatable incidents

## Color Legend

- Blue: ServiceNow source and trigger
- Gold: Local webhook and data collection
- Green: Splunk and AI enrichment
- Orange: Governance and control layer
- Teal: Write-back and action layer

## Presenter Script

This solution starts when a new incident is created in ServiceNow. A Business Rule immediately pushes the event to our local webhook through ngrok. The Python service then fetches the full incident, searches Splunk for supporting evidence, and sends the combined context to the LLM. Before writing anything back, guardrails check for low-signal tickets, confidence levels, and duplicate analyses. The final output is posted into ServiceNow as comments, evidence artifacts, and confidence-based assignment recommendations.

## Executive Summary Version

The platform turns new ServiceNow incidents into an automated triage pipeline. It enriches tickets with Splunk evidence, analyzes them with an LLM, applies confidence and manual-review guardrails, and writes structured recommendations back into ServiceNow for faster and safer operations.

## Slide Footer

Implementation stack:
ServiceNow, ngrok, Python, Flask, requests, Splunk, LangChain, ChatNVIDIA, NVIDIA AI Endpoints
