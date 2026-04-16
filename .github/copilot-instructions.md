# GitHub Copilot Instructions - ServiceNow Incident AI Analyzer

## Project Context

**ServiceNow Incident AI Analyzer** is a comprehensive agentic system that autonomously:
- Polls ServiceNow for new incidents every 5 minutes
- Analyzes incident content using NVIDIA GPT-OSS-120B LLM with extended reasoning
- Routes incidents intelligently to correct teams via auto-reassignment
- Prevents duplicate analysis via persistent JSON cache with ±10% confidence threshold
- Handles graceful shutdown cleanly (Ctrl+C within 5 seconds)

**Status:** Production Ready (Last Updated: April 2, 2026)

---

## Quick Start

```bash
# Activate environment
source .venv/bin/activate

# Create test incidents in wrong group (optional)
python3 setup_api_incidents.py

# Start the analyzer
python3 main.py

# Stop gracefully
Ctrl+C
```

---

## Key Features

### 1. Enhanced LLM with Extended Reasoning
- **Model:** NVIDIA `openai/gpt-oss-120b`
- **Latency:** 30-60+ seconds per analysis (slow but thorough)
- **Captures:** Extended reasoning from LLM reasoning_content

### 2. Intelligent Deduplication
- **Cache:** `logs/analyzed_incidents.json` (persistent)
- **Logic:** Only posts comments on first analysis or when confidence changes >10%
- **Result:** Prevents duplicate junk comments across cycles

### 3. Auto-Reassignment with Team Routing
- **Trigger:** Confidence ≥ 70%
- **Teams:** Database, Infrastructure, Application, Security
- **Routing:** Incident content → correct team based on LLM analysis

### 4. Graceful Shutdown
- **Mechanism:** Signal handlers (SIGINT/SIGTERM) + interruptible sleep
- **Response:** Exits cleanly within 5 seconds of Ctrl+C
- **Behavior:** Persists cache before exit

### 5. Rich Test Data
- **Setup Script:** `setup_api_incidents.py`
- **10 API Incidents:** Created with real HTTP error codes, payloads, headers, error IDs
- **Test Config:** All intentionally in wrong group ("IT Support") to test reassignment

---

## Critical Files

| File | Purpose |
|------|---------|
| `main.py` | Polling loop with graceful shutdown signals |
| `src/incident_processor.py` | Analysis orchestrator + dedup cache mgmt |
| `src/servicenow_client.py` | ServiceNow REST API wrapper (query, post, reassign) |
| `src/llm_client.py` | NVIDIA ChatNVIDIA wrapper |
| `logs/analyzed_incidents.json` | Deduplication cache (auto-created) |
| `config/config.yaml` | System configuration |
| `config/.env` | Credentials (git-ignored) |
| `COPILOT.md` | Comprehensive context for future development |

---

## Common Tasks

### Run Full Analysis Cycle
```bash
python3 main.py
# Polls every 5 min, analyzes, reassigns auto
Ctrl+C  # Clean exit
```

### Create Fresh Test Data
```bash
python3 setup_api_incidents.py
# Creates 10 API incidents in "IT Support" group
# Ready for reassignment testing
```

### Check Analysis Cache
```bash
cat logs/analyzed_incidents.json | jq .
# Shows all analyzed incidents with confidence scores
```

### View Processing Summary
```bash
tail -50 logs/incident_agent.log | grep "Summary"
# Shows metrics: comments posted/skipped, reassigned count
```

### Force Cleanup
```bash
pkill -9 -f "python.*main.py"  # Kill any hung process
rm logs/analyzed_incidents.json   # Clear cache
python3 setup_api_incidents.py    # Fresh data
```

---

## Architecture

```
main.py (polling loop)
  ↓
incident_processor.py (analyze + route)
  ├── Check cache (analyzed_incidents.json)
  ├── Send to LLM (NVIDIA GPT-OSS-120b)
  ├── Post comment if new/confidence changes >10%
  └── Reassign if confidence ≥ 70%
  ↓
servicenow_client.py (REST API)
  ├── get_incidents() → query ServiceNow
  ├── add_comment() → post analysis
  └── update_assignment_group() → reassign
  ↓
ServiceNow (incidents updated)
```

---

## Configuration

**config.yaml:**
```yaml
analysis:
  auto_reassign: true           # Enable routing
  confidence_threshold: 70      # Reassign if ≥ 70%
  comment_threshold: 10         # Repost if change > 10%

llm:
  model: openai/gpt-oss-120b   # NVIDIA endpoint
  temperature: 1.0              # More creative responses
  max_tokens: 4096
```

**Environment (.env):**
```
SERVICENOW_INSTANCE_URL=https://yourinstance.service-now.com
SERVICENOW_USERNAME=your_user
SERVICENOW_PASSWORD=your_pass
NVIDIA_API_KEY=your_key
```

---

## Testing Scenarios

### Test 1: Deduplication
```bash
python3 main.py  # Cycle 1: 3 incidents analyzed, comments posted
Ctrl+C
python3 main.py  # Cycle 2: Comments skipped (same incidents, same confidence)
```

### Test 2: Auto-Reassignment
```bash
python3 setup_api_incidents.py  # Create in "IT Support" (wrong)
python3 main.py                 # Check ServiceNow - should move to right teams
```

### Test 3: Graceful Shutdown
```bash
python3 main.py
sleep 3
Ctrl+C  # Should exit cleanly within 5 seconds
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Script won't stop | Press Ctrl+C (graceful shutdown implemented) |
| Duplicate comments | Check `logs/analyzed_incidents.json` cache |
| No reassignments | Check confidence scores (need ≥ 70%) |
| ServiceNow connection fails | Verify .env credentials, check logs |
| LLM responses slow | Expected (30-60s) - GPT-OSS-120b trades speed for reasoning |

---

## Development Tips

1. **Always check logs first:** `tail -100 logs/incident_agent.log`
2. **Verify cache:** `cat logs/analyzed_incidents.json | jq .`
3. **Test fresh setup:** `python3 setup_api_incidents.py && python3 main.py`
4. **Monitor graceful shutdown:** Process should exit within 5 seconds of Ctrl+C
5. **Watch metrics:** Look for "Comments Posted" and "Reassigned" counters in summary

---

## Key Code Locations

- **Deduplication logic:** `src/incident_processor.py` - `_is_incident_already_analyzed()`
- **Auto-reassignment:** `src/incident_processor.py` - lines ~238-245
- **Graceful shutdown:** `main.py` - `signal_handler()` + shutdown_requested flag
- **LLM analysis:** `src/incident_processor.py` - `_analyze_incident()`
- **Team routing:** `src/incident_processor.py` - knowledge base KB mapping

---

## For More Details

See **COPILOT.md** in project root for comprehensive context, architecture diagrams, performance metrics, and development notes.
