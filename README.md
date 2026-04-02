# ServiceNow Incident AI Analyzer

A production-ready agentic system that autonomously analyzes ServiceNow incidents using advanced LLM reasoning and intelligently routes them to the correct teams.

## ✨ Features

- **🧠 Advanced LLM Analysis** - Uses NVIDIA GPT-OSS-120B with extended reasoning for deep incident analysis
- **🎯 Intelligent Team Routing** - Auto-reassigns incidents to correct teams based on confidence scores (Database, Infrastructure, Application, Security)
- **♻️ Smart Deduplication** - Persistent cache prevents duplicate comments with ±10% confidence threshold
- **🛑 Graceful Shutdown** - Clean exit with Ctrl+C within 5 seconds
- **🔄 Auto-Polling** - Checks ServiceNow every 5 minutes for new incidents
- **📊 Rich Test Data** - 10 API-focused incidents with realistic HTTP errors, status codes, and payloads for testing

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/ServiceNow-Incident-AI-Analyzer.git
cd ServiceNow-Incident-AI-Analyzer
```

### 2. Setup Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config/.env.example config/.env
# Edit config/.env with your credentials
```

### 3. Create Test Data (Optional)
```bash
python3 setup_api_incidents.py
```
This creates 10 API-focused incidents in "IT Support" group (intentionally wrong) to test auto-reassignment.

### 4. Run the Analyzer
```bash
python3 main.py
```

### 5. Stop Gracefully
```bash
Ctrl+C  # Exits cleanly within 5 seconds
```

## 📋 Configuration

### Environment Variables (.env)
```env
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
NVIDIA_API_KEY=your_nvidia_api_key
LANGCHAIN_API_KEY=your_langchain_api_key (optional)
```

### Configuration (config/config.yaml)
```yaml
analysis:
  auto_reassign: true           # Enable auto-reassignment
  confidence_threshold: 70      # Minimum confidence for reassignment
  comment_threshold: 10         # Repost if confidence changes >10%

llm:
  model: openai/gpt-oss-120b
  temperature: 1.0
  top_p: 1.0
  max_tokens: 4096
```

## 📁 Project Structure

```
Snow_TicketAssignment/
├── main.py                     # Main polling loop
├── setup_api_incidents.py      # Test data setup script
├── COPILOT.md                  # Comprehensive development context
├── README.md                   # This file
├── config/
│   ├── config.yaml            # Configuration
│   └── .env                    # Credentials (git-ignored)
├── src/
│   ├── servicenow_client.py   # ServiceNow REST API wrapper
│   ├── incident_processor.py  # Analysis & routing orchestrator
│   ├── llm_client.py          # NVIDIA ChatNVIDIA wrapper
│   ├── mock_kb.py             # Mock knowledge base
│   └── utils.py               # Helper functions
├── logs/
│   ├── incident_agent.log     # Main agent log
│   ├── llm_analysis.log       # LLM analysis log
│   └── analyzed_incidents.json # Deduplication cache
└── .venv/                      # Python environment
```

## 🧪 Testing

### Test 1: Deduplication
```bash
python3 main.py
# Wait 5 minutes
Ctrl+C

python3 main.py
# Check logs - should show "Comments Skipped: X"
```
**Expected:** Comments posted in cycle 1, skipped in cycle 2 for same incidents.

### Test 2: Auto-Reassignment
```bash
python3 setup_api_incidents.py
python3 main.py
# Check ServiceNow - incidents should move to correct teams
```
**Expected:** 
- Database issues → Database Team
- API gateway issues → Infrastructure Team
- API/webhook issues → Application Team
- Auth/security issues → Security Team

### Test 3: Graceful Shutdown
```bash
python3 main.py
sleep 3
Ctrl+C  # Should exit cleanly within 5 seconds
```

## 📊 Data Flow

```
ServiceNow (Incident Source)
    ↓ 
[main.py] - Polls every 5 minutes
    ↓
[incident_processor.py] - Analyzes & routes
  ├── Check dedup cache
  ├── Send to LLM (NVIDIA GPT-OSS-120B)
  ├── Post comment if new/changed
  └── Reassign if confidence ≥ 70%
    ↓
[servicenow_client.py] - REST API calls
    ↓
ServiceNow (Updated incidents & assignments)
```

## 🔄 How It Works

1. **Polling** - Main loop checks ServiceNow every 5 minutes for new incidents
2. **Deduplication** - Checks persistent cache (`logs/analyzed_incidents.json`) to skip already-analyzed incidents
3. **Analysis** - Sends incident description to NVIDIA GPT-OSS-120B for deep analysis
   - Determines incident category/team
   - Calculates confidence score
   - Identifies root cause
4. **Comment** - Posts analysis as incident comment (only if new or significant change >10%)
5. **Routing** - Auto-reassigns to correct team if confidence ≥ 70%
6. **Caching** - Persists analysis for future cycles

## 📈 Processing Summary

Each cycle produces:
```
Incidents: 3 analyzed, 0 errors
Comments: Posted: 2 | Skipped: 1
Reassigned: 2
```

## 🔐 Security

- **Never commit .env** - Credentials are git-ignored
- **API Keys** - Use environment variables via python-dotenv
- **Logs** - May contain incident details, keep secure
- **Deduplication cache** - Local only, never synced

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Script won't stop | Press Ctrl+C (graceful shutdown implemented) |
| Duplicate comments | Check `logs/analyzed_incidents.json` cache |
| No reassignments | Verify confidence ≥ 70%, check logs |
| ServiceNow connection fails | Verify .env credentials and instance URL |
| LLM responses slow | Expected (30-60s) - GPT-OSS-120B provides detailed reasoning |

## 📚 Documentation

- **[COPILOT.md](COPILOT.md)** - Comprehensive development context (456 lines)
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Quick reference guide
- **[Logs](logs/)** - Agent and LLM analysis logs

## 🎯 Key Features Explained

### Enhanced LLM with Extended Reasoning
- Uses NVIDIA `openai/gpt-oss-120b` model
- Captures extended reasoning process (not just final answer)
- Temperature: 1.0 for creative, detailed responses
- Latency: 30-60+ seconds (slower but more thorough)

### Intelligent Deduplication
- File: `logs/analyzed_incidents.json`
- Only posts comments on first analysis
- Re-posts if confidence changes by >10%
- Prevents duplicate junk comments

### Auto-Reassignment with Team Routing
- Trigger: Confidence score ≥ 70%
- Routes to: Database, Infrastructure, Application, Security teams
- Based on incident content analysis

### Graceful Shutdown
- Signal handlers for SIGINT (Ctrl+C) and SIGTERM
- Process exits cleanly within 5 seconds
- Persists cache before shutdown

## 📦 Dependencies

```
langchain
langgraph
langchain-nvidia-ai-endpoints
requests
python-dotenv
pydantic
pyyaml
```

See `requirements.txt` for exact versions.

## 📝 API Integration

### ServiceNow REST API
- Endpoint: `/api/now/v2/table/incident`
- Authentication: Basic Auth with username/password
- Operations: Query, Create, Update, Delete incidents

### NVIDIA Foundation Models API
- Endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`
- Model: `openai/gpt-oss-120b`
- Auth: API key via NVIDIA_API_KEY

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Built as a production-ready incident automation system for ServiceNow environments.

## 🔗 Resources

- [NVIDIA Foundation Models](https://build.nvidia.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [ServiceNow REST API](https://developer.servicenow.com/dev_portal)
- [COPILOT.md](COPILOT.md) - Comprehensive project context

## 📞 Support

For issues, questions, or suggestions:
1. Check [COPILOT.md](COPILOT.md) for detailed context
2. Review [Troubleshooting](#-troubleshooting) section
3. Check logs in `logs/` directory
4. Open an issue on GitHub

---

**Last Updated:** April 2, 2026  
**Status:** Production Ready
