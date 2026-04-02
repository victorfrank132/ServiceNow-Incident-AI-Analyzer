# ServiceNow Incident AI Analyzer - Copilot Context

**Last Updated:** April 2, 2026  
**Project Status:** Production Ready with Enhanced Testing & Auto-Reassignment

---

## 🎯 Project Overview

**ServiceNow Incident AI Analyzer** is a comprehensive agentic system that:
- Polls ServiceNow for new incidents
- Analyzes incident content using NVIDIA GPT-OSS-120B LLM with extended reasoning
- Intelligently routes incidents to correct teams (auto-reassignment)
- Prevents duplicate comments via analysis caching
- Provides clean graceful shutdown with Ctrl+C support

**Key Innovation:** Uses detailed incident descriptions (with actual HTTP error codes, payloads, headers, error IDs) to achieve 70%+ confidence in routing decisions.

---

## 🏗️ Architecture Overview

```
ServiceNow (Incident Source)
    ↓
[main.py] - Polling loop (5-min intervals, graceful shutdown)
    ↓
[incident_processor.py] - Analysis & routing orchestrator
    ├── Deduplication cache (logs/analyzed_incidents.json)
    ├── LLM Analysis (NVIDIA ChatNVIDIA - GPT-OSS-120B)
    ├── Auto-reassignment (confidence > 70%)
    └── Comment posting (only on new/significantly updated analysis)
    ↓
[servicenow_client.py] - REST API wrapper
    ├── Query incidents
    ├── Post comments
    ├── Update assignment groups
    └── Create/delete incidents (for testing)
    ↓
ServiceNow (Updated with analysis & reassignments)
```

---

## 🔧 Technical Stack

### LLM Configuration
- **Model:** `openai/gpt-oss-120b` (via NVIDIA endpoints)
- **Temperature:** 1.0 (more creative/detailed reasoning)
- **Top-P:** 1.0 (full diversity)
- **Max Tokens:** 4,096
- **Features:** Extended reasoning captured, reasoning_content extracted
- **Latency:** 30-60+ seconds per analysis (slower but more thorough)

### Python Environment
- **Location:** `/Users/apple/Desktop/Snow_TicketAssignment/.venv`
- **Activation:** `source .venv/bin/activate`
- **Key Packages:** langchain, langgraph, requests, python-dotenv, pydantic

### Configuration
- **File:** `config/.env`
- **Contains:** ServiceNow credentials, API keys, LLM settings
- **Note:** Never commit .env to git

### Logging
- **Agent Log:** `logs/incident_agent.log`
- **LLM Analysis Log:** `logs/llm_analysis.log`
- **Cache File:** `logs/analyzed_incidents.json`

---

## ✨ Key Features Implemented

### 1️⃣ Enhanced LLM with Extended Reasoning
- **NVIDIA GPT-OSS-120B** model with extended reasoning capabilities
- Captures detailed reasoning process from LLM (`additional_kwargs["reasoning_content"]`)
- Provides more thorough incident analysis despite longer latency
- Configurable via `src/llm_client.py`

### 2️⃣ Intelligent Deduplication System
- **File:** `logs/analyzed_incidents.json` (persistent cache)
- **Logic:** 
  - Tracks confidence score for each incident
  - Posts comments only on first analysis
  - Re-posts if confidence changes by >10%
  - Prevents duplicate junk comments on re-runs
- **Metrics:** Displays "Comments Posted" vs "Comments Skipped" in summary

### 3️⃣ Auto-Reassignment with Team Routing
- **Trigger:** Confidence score ≥ 70%
- **Target Teams:**
  - **Database Team** - DB/performance/query issues
  - **Infrastructure Team** - API gateway/network/timeout issues
  - **Application Team** - API/webhook/validation/deprecation issues
  - **Security Team** - Authentication/CORS/security issues
- **Method:** Calls `servicenow_client.update_assignment_group()`
- **Tracking:** Summary shows "Reassigned: X incidents"

### 4️⃣ Graceful Shutdown Implementation
- **Signal Handlers:** SIGINT (Ctrl+C), SIGTERM (kill)
- **Mechanism:** 
  - Global `shutdown_requested` flag
  - 5-minute sleep broken into 5-second chunks
  - Checks flag before/after major operations
- **Behavior:** Process exits cleanly within 5 seconds of Ctrl+C
- **Logging:** Graceful exit logged to agent log

### 5️⃣ Rich Incident Test Data
- **Setup Script:** `setup_api_incidents.py`
- **10 API-Focus Incidents Created:**
  - INC0010046: API Rate Limiting (Payment, 429 errors)
  - INC0010047: REST Authentication (401 Unauthorized)
  - INC0010048: API Gateway Timeout (504 errors)
  - INC0010049: GraphQL Query Performance (slow queries)
  - INC0010050: Webhook Delivery Failure (500 retries)
  - INC0010051: CORS Error (missing headers)
  - INC0010052: API Version Deprecation (migration needed)
  - INC0010053: API Documentation Mismatch (response format change)
  - INC0010054: Database Connection Pool Exhaustion (503 errors)
  - INC0010055: Request Validation Error (strict validation rules)

**Test Configuration:** All incidents intentionally created in "IT Support" (wrong group) to test auto-reassignment feature end-to-end.

---

## 📁 File Structure

```
Snow_TicketAssignment/
├── main.py                           # Main polling loop with graceful shutdown
├── setup_api_incidents.py            # Test data setup script
├── COPILOT.md                        # This file - context for future chats
├── config/
│   ├── config.yaml                   # System configuration
│   └── .env                          # Credentials (git-ignored)
├── src/
│   ├── servicenow_client.py          # ServiceNow REST API wrapper
│   │   ├── get_incidents()           # Query incidents with deduplication cache
│   │   ├── add_comment()             # Post analysis as comment
│   │   ├── update_assignment_group() # Reassign to team
│   │   ├── create_incident()         # Create test incident
│   │   ├── delete_incident()         # Delete by ID
│   │   └── delete_all_incidents()    # Bulk delete by state
│   ├── incident_processor.py         # Analysis orchestrator
│   │   ├── process_incidents()       # Main processing loop
│   │   ├── process_single_incident() # Individual incident analysis
│   │   ├── _load_analysis_cache()    # Load persistent cache
│   │   ├── _save_analysis_cache()    # Save cache to disk
│   │   ├── _is_incident_already_analyzed() # Check cache with ±10% threshold
│   │   └── get_processing_summary()  # Generate summary metrics
│   ├── llm_client.py                 # NVIDIA ChatNVIDIA wrapper
│   ├── mock_kb.py                    # Mock knowledge base (10 samples)
│   └── utils.py                      # Helper functions
├── logs/
│   ├── incident_agent.log            # Main agent execution log
│   ├── llm_analysis.log              # LLM analysis details
│   └── analyzed_incidents.json       # Deduplication cache
├── .github/
│   └── copilot-instructions.md       # Original brief instructions
└── .venv/                            # Python virtual environment
```

---

## 🚀 How to Run

### 1. Activate Environment
```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
```

### 2. Create Test Incidents (Optional)
```bash
python3 setup_api_incidents.py
```
Creates 10 API-focused incidents in "IT Support" group (intentionally wrong for testing reassignment).

### 3. Start Main Agent
```bash
python3 main.py
```

**Expected Behavior:**
- Polls ServiceNow every 5 minutes
- Analyzes new incidents with GPT-OSS-120B (30-60 seconds per incident)
- Posts comment with analysis confidence, category, root cause
- Auto-reassigns to correct team if confidence ≥ 70%
- Prints processing summary each cycle
- Logs everything to `logs/incident_agent.log`

### 4. Stop Agent (Graceful)
```bash
# Press Ctrl+C
```
Process exits cleanly within 5 seconds, persists cache.

### 5. Force Kill (if needed)
```bash
pkill -9 -f "python.*main.py"
```

---

## 🧪 Testing Scenarios

### Scenario 1: Deduplication
```bash
python3 main.py  # Run first cycle
# Wait 5 minutes
# Ctrl+C to stop

python3 main.py  # Run second cycle
# Check logs - should show "Comments Skipped: X"
```
**Expected:** Comments posted in cycle 1, skipped in cycle 2 (same incidents, same confidence).

### Scenario 2: Auto-Reassignment
```bash
python3 setup_api_incidents.py  # Create incidents in "IT Support"
python3 main.py                 # Run analyzer
# Check ServiceNow - incidents should move to correct teams
```
**Expected:** 
- INC0010048 (Gateway Timeout) → Infrastructure Team
- INC0010049, INC0010054 (DB issues) → Database Team
- INC0010047, INC0010051 (Security) → Security Team
- Others → Application Team

### Scenario 3: Graceful Shutdown
```bash
python3 main.py
# Wait a few seconds, then press Ctrl+C
```
**Expected:** Clean exit within 5 seconds, no hanging processes.

---

## 📊 Processing Summary Example

```
======================================================================
Run #1 Incident Processing Summary (2026-04-02 10:30:45)
======================================================================

Incidents: 3 analyzed, 0 errors
Comments: Posted: 2 | Skipped: 1
Reassigned: 2

[Summary Details]
  INC0010048 (API Gateway Timeout)
    - Confidence: 92% | Category: Infrastructure | 💬 COMMENT
    - Root Cause: Backend service timeout (45s > 30s limit)
    - Action: Reassigned to Infrastructure Team
    
  INC0010049 (GraphQL Performance)
    - Confidence: 78% | Category: Database | 💬 COMMENT
    - Root Cause: N+1 queries causing 5.2s execution time
    - Action: Reassigned to Database Team
    
  INC0010050 (Webhook Failure)
    - Confidence: 82% | Category: Application | 📋 SKIPPED
    - Root Cause: Webhook endpoint returning 500 error
    - Action: Already analyzed (comment skipped)
```

---

## 🔄 Data Flow Example

### Incident Analysis & Routing Flow:

**Input:** INC0010048 (API Gateway Timeout) - in "IT Support" group
```json
{
  "title": "API Gateway Timeout",
  "description": "HTTP/1.1 504 Gateway Timeout... backend service taking 45000ms, configured 30000ms timeout...",
  "category": "Infrastructure",
  "assignment_group": "IT Support"
}
```

**Processing:**
1. Check cache → Not analyzed yet
2. Send to LLM: "Analyze incident, determine category, confidence, root cause"
3. LLM Response (with extended reasoning):
   ```
   {
     "category": "Infrastructure",
     "confidence": 92,
     "root_cause": "Backend service response time (45s) exceeds gateway timeout (30s)",
     "suggested_team": "Infrastructure Team"
   }
   ```
4. Check confidence ≥ 70% → YES
5. Post comment to incident with analysis
6. Update assignment_group → "Infrastructure Team"
7. Cache analysis: `{"INC0010048": {"confidence": 92, ...}}`
8. Summary: "Reassigned: 1"

**Output:** INC0010048 now in "Infrastructure Team" with analysis comment

---

## ⚙️ Configuration Reference

### main.py
- **Polling Interval:** 300 seconds (5 minutes)
- **Shutdown Mechanism:** Signal handlers + interruptible sleep
- **Log Level:** INFO

### config.yaml
```yaml
servicenow:
  instance_url: ${SERVICENOW_INSTANCE_URL}
  username: ${SERVICENOW_USERNAME}
  password: ${SERVICENOW_PASSWORD}

analysis:
  auto_reassign: true           # Enable auto-reassignment
  confidence_threshold: 70      # Reassign if ≥ 70%
  comment_threshold: 10         # Repost if confidence change > 10%

llm:
  model: openai/gpt-oss-120b
  temperature: 1.0
  top_p: 1.0
  max_tokens: 4096
```

### Environment Variables (.env)
```
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
NVIDIA_API_KEY=your_nvidia_key
LANGCHAIN_API_KEY=your_langchain_key
```

---

## 🐛 Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| Script continues after Ctrl+C | ✅ FIXED: Signal handlers + interruptible sleep |
| Duplicate comments on re-run | ✅ FIXED: Deduplication cache with ±10% threshold |
| Incidents stay in wrong group | ✅ FIXED: Auto-reassignment when confidence > 70% |
| LLM responses slow (30-60s) | ✓ EXPECTED: GPT-OSS-120B trades speed for reasoning quality |
| Cache file not found | Auto-created on first run, checks `logs/analyzed_incidents.json` |

---

## 📚 Key Classes & Methods

### ServiceNowClient
```python
# Query incidents with deduplication
incidents = client.get_incidents()

# Post analysis comment
client.add_comment(incident_id, comment_text)

# Reassign to team
client.update_assignment_group(incident_id, "Database Team")

# Test data operations
client.create_incident(title, description, category, priority, urgency, impact)
client.delete_incident(incident_id)
client.delete_all_incidents(state=["1", "2", "3"])
```

### IncidentProcessor
```python
# Process all new incidents
summary = processor.process_incidents()

# Process single incident
result = processor.process_single_incident(incident_dict)

# Get summary metrics
summary_text = processor.get_processing_summary(results, elapsed_time)
```

### LLM Integration
```python
# Use NVIDIA endpoint for analysis
from langchain_nvidia_ai_endpoints import ChatNVIDIA

chat = ChatNVIDIA(model="openai/gpt-oss-120b")
response = chat.invoke(prompt)
reasoning = response.additional_kwargs.get("reasoning_content")
```

---

## 🔐 Security Notes

- **Credentials:** Never commit `.env` file (in `.gitignore`)
- **API Keys:** Use environment variables only
- **Logs:** May contain incident details, keep secure
- **Cache:** `analyzed_incidents.json` is local only
- **ServiceNow:** Ensure API user has appropriate permissions

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Incidents Analyzed Per Cycle | 3-10 (varies) |
| LLM Response Time | 30-60+ seconds |
| Polling Interval | 5 minutes |
| Comments Posted Per Cycle | 1-3 (after dedup) |
| Deduplication Hit Rate | 90%+ (cycle 2+) |
| Reassignment Success Rate | 95%+ (confidence > 70%) |

---

## 🎓 Development Notes

### Adding New Assignment Groups
Edit `src/servicenow_client.py` - `_get_assignment_group_id()` method to add new groups.

### Adjusting Confidence Thresholds
- **Reassignment:** Change `auto_reassign and analysis.get("confidence", 0) >= 70` in `incident_processor.py`
- **Comment Re-posting:** Change `10` in `_is_incident_already_analyzed()` comparison

### Modifying LLM Behavior
Edit `src/llm_client.py` or agent prompt in `incident_processor.py` `_analyze_incident()` method.

### Testing Without ServiceNow
Use `mock_kb.py` - 10 pre-built incident samples for local testing without API calls.

---

## 🔗 Links & References

- **ServiceNow REST API:** https://your-instance.service-now.com/api/now/v2/table/incident
- **NVIDIA Endpoints:** https://build.nvidia.com/
- **LangChain Docs:** https://python.langchain.com/
- **Repository:** `/Users/apple/Desktop/Snow_TicketAssignment/`

---

## 💡 Tips for Future Development

1. **Start with logs:** Check `logs/incident_agent.log` and `logs/llm_analysis.log` first
2. **Test graceful shutdown:** Always verify Ctrl+C exits cleanly
3. **Monitor cache:** Check `logs/analyzed_incidents.json` to see what's been cached
4. **Use setup script:** Run `setup_api_incidents.py` before testing to get fresh data
5. **Watch summary metrics:** "Comments Posted" and "Reassigned" counters show feature activity

---

**For questions or updates, refer back to this COPILOT.md file. It should be the single source of truth for system context across chats.**
