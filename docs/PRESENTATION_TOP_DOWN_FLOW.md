# Top-Down Presentation Flow

## Best Use

Use this version when you want a vertical infographic for PowerPoint or Word with clear color coding and an explicit parallel-runtime section.

## Design Intent

- Top to bottom reading order
- Parallel startup layer at the top
- Main execution path in the center
- Supporting systems shown as side-linked dependencies
- Color-coded zones for easier storytelling

## Color Legend

- Blue: ServiceNow source and trigger layer
- Yellow: Local runtime and network path
- Green: External enrichment and intelligence
- Orange: Guardrails, confidence logic, and deduplication
- Teal: ServiceNow write-back and business action
- Gray: Logs, cache, and persistent artifacts
- Purple border: Parallel processes or always-on runtime pieces

## PPT Box Order

### Parallel Layer
1. Terminal 1: `start.py`
2. Terminal 2: `ngrok http 8081`

These two run in parallel.

### Main Vertical Flow
3. Incident Created in ServiceNow
4. Business Rule Reads Webhook URL
5. ServiceNow Sends HTTPS Event to ngrok
6. ngrok Forwards Request to Flask Receiver
7. Fetch Full Incident from ServiceNow
8. Search Splunk for Evidence
9. Build AI Context with KB + Evidence
10. Run LLM Analysis
11. Apply Guardrails and Deduplication
12. Post Comment / Evidence / Reassignment back to ServiceNow

## Presenter Notes

- Start by calling out that two local runtime components must be running together: the Python webhook receiver and the ngrok tunnel.
- Then explain that ServiceNow only talks to the public ngrok URL, while ngrok forwards that traffic into the local Flask app.
- After the receiver gets the event, the processing becomes sequential: fetch incident, search Splunk, generate AI analysis, apply guardrails, and write back to ServiceNow.
- Emphasize that guardrails prevent risky automation on low-signal or duplicate incidents.

## Mermaid Source

```mermaid
flowchart TB
    subgraph P["Parallel Runtime Setup"]
        direction LR
        P1["Terminal 1<br/>start.py<br/>Python + Flask Receiver"]
        P2["Terminal 2<br/>ngrok http 8081<br/>Public HTTPS Tunnel"]
        P2 -->|"Forwards public traffic to localhost:8081"| P1
    end

    A["Incident Created<br/>ServiceNow Incident Table"]
    B["After-Insert Trigger<br/>Business Rule + System Property"]
    C["Send Webhook Event<br/>HTTPS POST to ngrok URL"]
    D["Receive Webhook Locally<br/>Flask Receiver"]
    E["Fetch Full Incident<br/>ServiceNow REST API + requests"]
    F["Retrieve Splunk Evidence<br/>SplunkClient + Splunk REST API"]
    G["Build AI Context<br/>Incident + KB + Evidence"]
    H["Run LLM Analysis<br/>LangChain + ChatNVIDIA + NVIDIA AI Endpoints"]
    I{"Low Signal / Low Confidence / Duplicate?"}
    J["Manual Review Fallback<br/>Confidence Thresholds<br/>analyzed_incidents.json"]
    K["Write Back to ServiceNow<br/>Comment + Work Note + Attachment + Reassignment"]
    L[("Logs and Cache<br/>webhook.log<br/>llm_analysis.log<br/>analyzed_incidents.json")]

    A --> B --> C
    P2 --> C
    C --> D
    P1 --> D
    D --> E --> F --> G --> H --> I
    I -- "Yes" --> J --> K
    I -- "No" --> K
    H -. "LLM trace" .-> L
    I -. "Cache / dedupe check" .-> L
    K -. "Runtime / audit logs" .-> L

    classDef parallel fill:#F4ECFF,stroke:#8B5CF6,stroke-width:2px,color:#111827;
    classDef servicenow fill:#DBEAFE,stroke:#2563EB,stroke-width:1.5px,color:#111827;
    classDef local fill:#FEF3C7,stroke:#D97706,stroke-width:1.5px,color:#111827;
    classDef enrich fill:#DCFCE7,stroke:#16A34A,stroke-width:1.5px,color:#111827;
    classDef guard fill:#FED7AA,stroke:#EA580C,stroke-width:1.5px,color:#111827;
    classDef writeback fill:#CCFBF1,stroke:#0F766E,stroke-width:1.5px,color:#111827;
    classDef artifact fill:#E5E7EB,stroke:#6B7280,stroke-width:1.5px,color:#111827;

    class P1,P2 parallel;
    class A,B,C servicenow;
    class D,E local;
    class F,G,H enrich;
    class I,J guard;
    class K writeback;
    class L artifact;
```

## Short Caption

Two local processes run in parallel: the Flask webhook receiver and the ngrok tunnel. ServiceNow sends incident events to ngrok, ngrok forwards them to Flask, and the application then enriches, analyzes, guards, and writes the result back into ServiceNow.

## Slide Footer

Implementation stack:
ServiceNow, Business Rule, System Property, ngrok, Python, Flask, requests, Splunk, LangChain, ChatNVIDIA, NVIDIA AI Endpoints
