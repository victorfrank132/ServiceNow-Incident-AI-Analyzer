# Quick Start Guide - ServiceNow Incident AI Analyzer

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
pip install -r requirements.txt
```

### 2. Configure Credentials
```bash
cp config/.env.example config/.env
```
Edit `config/.env` and fill in:
- `SERVICENOW_INSTANCE_URL` - Your ServiceNow instance (e.g., https://dev12345.service-now.com)
- `SERVICENOW_CLIENT_ID` - Your OAuth client ID
- `SERVICENOW_CLIENT_SECRET` - Your OAuth client secret  
- `OPENAI_API_KEY` - Your OpenAI API key

### 3. Configure Team Mappings (Optional)
Edit `config/team_mappings.json` to map incident categories to your assignment groups:
```json
{
  "Database": "Your-DBA-Team-Name",
  "Infrastructure": "Your-Infra-Team-Name"
}
```

## 🚀 Running the Agent

### Start the polling loop:
```bash
/Users/apple/Desktop/Snow_TicketAssignment/.venv/bin/python main.py
```

The agent will:
- Poll ServiceNow every 5 minutes for new incidents
- Analyze each incident using GPT-4
- Add AI analysis comments to tickets
- Automatically reassign to appropriate teams
- Log all actions to `logs/incident_agent.log`

### Run Tests:
```bash
/Users/apple/Desktop/Snow_TicketAssignment/.venv/bin/python -m unittest discover -s tests
```

## 📊 Project Components

| Component | Purpose |
|-----------|---------|
| `servicenow_client.py` | ServiceNow REST API wrapper |
| `incident_analyzer.py` | GPT-4 LLM analyzer with KB search |
| `incident_processor.py` | Main orchestration workflow |
| `mock_kb.py` | 10 mock incident examples |
| `logging.py` | JSON audit logging |
| `main.py` | Entry point with polling loop |

## 🔍 Example Incident Flow

1. **Fetch**: Agent finds new incident → "Database connection timeout on prod server"
2. **Analyze**: GPT-4 analyzes + searches KB for similar incidents
3. **Comment**: Adds analysis with root cause, steps, and similar past incidents
4. **Reassign**: Automatically routes to "DBA-Team" 
5. **Log**: Tracks confidence score, reasoning, and outcome

## 📝 Configuration Files

### `config/config.yaml`
- Polling interval (default: 300s / 5 min)
- Max incidents per run (default: 10)
- Confidence threshold (default: 0.6)
- Logging level

### `config/team_mappings.json`
- Maps incident category → ServiceNow assignment group
- Example: "Database" → "DBA-Team"

### `config/.env`
- ServiceNow credentials
- OpenAI API key

## 🧪 Testing

All 14 unit tests pass:
```bash
/Users/apple/Desktop/Snow_TicketAssignment/.venv/bin/python -m unittest discover -s tests -v
```

Tests cover:
- ✅ ServiceNow client API wrapper
- ✅ Mock knowledge base with 10 sample incidents
- ✅ Incident analyzer and formatting
- ✅ Error handling and fallbacks

## 📋 Feature Checklist

- ✅ Polls ServiceNow for new incidents
- ✅ Analyzes with GPT-4 LLM
- ✅ Searches mock knowledge base for similar incidents
- ✅ Adds AI-generated analysis comments
- ✅ Automatically reassigns to teams
- ✅ JSON audit logging
- ✅ Rate limiting and error handling
- ✅ Configurable team mappings
- ✅ Comprehensive test suite

## 🎯 Next Steps

1. Test against your ServiceNow sandbox instance
2. Tune team_mappings.json for your assignment groups
3. Adjust config.yaml polling interval if needed
4. Run in background (systemd/cron/Docker)
5. Monitor logs/incident_agent.log for agent decisions

## 📞 Troubleshooting

**"No incidents found"**
- Check incident states in ServiceNow (agent looks for state 1=New, 2=In Progress)

**"ServiceNow connection failed"**
- Verify credentials in config/.env
- Check OAuth token has required API scope

**"GPT-4 not available"**
- Ensure OpenAI account has GPT-4 access
- Check API key is valid and not rate-limited

For full details, see [README.md](README.md)
