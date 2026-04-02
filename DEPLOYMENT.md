# 🚀 ServiceNow Incident AI Analyzer - Setup Complete!

## ✅ Your Setup Status

- **Instance**: https://dev218421.service-now.com
- **Auth**: Basic Authentication (username: admin)
- **Connection**: ✅ **VERIFIED**
- **Available Assignment Groups**: 20 (Network, Database, Application Development, etc.)
- **Current Incidents**: 5 recent (3 in "In Progress" state)
- **Incident Categories**: 4 (Hardware, database, inquiry, software)

## 🎯 Next Steps

### 1. Add Your OpenAI API Key

Edit `config/.env` and add your OpenAI GPT-4 API key:

```bash
# Get your API key from: https://platform.openai.com/account/api-keys
OPENAI_API_KEY=sk-your-key-here
```

### 2. Run the Agent

Start the incident analysis loop:

```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
python main.py
```

What it does:
- Polls every 5 minutes for **New** incidents (state=1)
- Uses GPT-4 to analyze each incident
- Searches knowledge base for similar past incidents
- Adds AI analysis comment to the ticket
- Automatically reassigns to the appropriate team
- Logs all actions with JSON formatting

### 3. Create Test Incidents (Optional)

To see the agent in action, create incidents in ServiceNow with state="New":
- Title: "Database connection timeout on prod server"
- Description: Details about the connection issue
- State: New (it will move to In Progress when assigned)

The agent will:
1. Fetch the incident
2. Analyze it with GPT-4
3. Add a detailed analysis comment
4. Reassign to the "Database" team

### 4. Monitor Activity

Watch the logs in real-time:

```bash
tail -f logs/incident_agent.log
```

Each log entry is JSON with timestamp, incident ID, analysis, and action taken.

## 📋 Knowledge Base

The agent searches a **mock knowledge base** with 10 sample incidents:

| Category | Examples |
|----------|----------|
| Database | Connection timeouts, memory leaks, pool exhaustion |
| Infrastructure | High CPU, disk space, server crashes |
| Networking | Connectivity loss, firewall issues, routing problems |
| Application | Startup failures, crashes, performance issues |

When you're ready, this can be replaced with your actual ServiceNow KB module or a vector database.

## 🔧 Configuration

### `config/config.yaml`

```yaml
servicenow:
  instance_url: "https://dev218421.service-now.com"
  auth_type: "basic"
  polling_interval_seconds: 300  # 5 minutes

incident_processing:
  max_incidents_per_run: 10      # Process up to 10 per polling cycle
  include_state: ["1", "2"]      # Monitor New and In Progress
  
analysis:
  enabled: true
  auto_reassign: true             # Automatic reassignment enabled
  confidence_threshold: 0.6       # Reassign if confidence > 60%
```

### `config/team_mappings.json`

Maps incident categories to your assignment groups:

```json
{
  "Database": "Database",
  "Network": "Network",
  "Software": "Incident Management",
  "default": "Incident Management"
}
```

Customize this to match your organization's routing rules.

### `config/.env`

```dotenv
SERVICENOW_INSTANCE_URL=https://dev218421.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=W2FBr!6-gjZw
OPENAI_API_KEY=sk-your-api-key-here
```

## 🧪 Testing

### Test Connection
```bash
python test_connection.py
```
✅ Verifies ServiceNow credentials work

### Explore Your Data
```bash
python explore_snow.py
```
Shows available incidents, groups, and categories

### Run Unit Tests
```bash
python -m unittest discover -s tests -v
```
All 14 tests should pass ✓

## 📊 Example Incident Flow

**Before AI Agent:**
```
Incident INC0000055: "SAP Sales app is not accessible"
State: In Progress
Assignment Group: (empty handoff)
Description: Users cannot access SAP
```

**After AI Agent:**
```
Incident INC0000055: "SAP Sales app is not accessible"
State: In Progress
Assignment Group: Application Development ← Auto-assigned!

[AI Analysis Comment Added]
Category: Application
Confidence: 85%
Root Cause: Application service may be down or misconfigured
Steps: 1. Check SAP service status 2. Review error logs 3. Restart if needed
Similar Past Incidents: Memory Leak in Service, Application Crashes on Startup
```

## 🔍 Troubleshooting

### "OpenAI API key not found"
```bash
# Add to config/.env
OPENAI_API_KEY=sk-your-key-from-platform.openai.com
```

### "No incidents processed"
The agent looks for incidents in state "New" (state=1) or "In Progress" (state=2).
- If none are found, the agent waits for the next polling cycle
- Create test incidents with state="New" to trigger processing

### "Low confidence analyses"
If analysis confidence is too low:
- Increase incident description detail
- Adjust confidence_threshold in config.yaml
- Review KB keywords in mock_kb.py

### "Reassignment not working"
- Check assignment group name in team_mappings.json exists in ServiceNow
- Run `python explore_snow.py` to see available groups
- Ensure admin user has permission to reassign incidents

## 📈 Production Ready Features

- ✅ Polling loop with configurable intervals
- ✅ Rate limiting and error handling
- ✅ JSON audit logging with timestamps
- ✅ Fallback logic (retries, defaults)
- ✅ Unit test coverage (14 tests)
- ✅ Credentials in .env (not hardcoded)
- ✅ Configurable team mappings
- ✅ Confidence-based auto-reassignment

## 🚀 Advanced Usage

### Deploy as Background Service

**Option 1: macOS (launchd)**
```bash
# Create ~/Library/LaunchAgents/com.servicenow.analyzer.plist
# Add the agent to auto-start on login
```

**Option 2: Linux (systemd)**
```bash
# Create /etc/systemd/system/snow-analyzer.service
# Enable: systemctl enable snow-analyzer
```

**Option 3: Docker**
```bash
docker build -t snow-analyzer .
docker run -d --env-file config/.env snow-analyzer
```

### Integrate with Slack
Add Slack notifications when incidents are analyzed:
```python
# In incident_processor.py, add:
send_slack_message(f"Analyzed {incident_num}, reassigned to {team}")
```

### Real-Time Webhooks
Replace polling with ServiceNow webhooks for instant processing:
```python
# In webhook_receiver.py
@app.post("/webhook/incident")
def handle_incident_webhook(incident_data):
    # Process immediately instead of waiting 5 min
```

## 📞 Support

For detailed documentation, see:
- [README.md](README.md) - Full feature documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick reference
- [config/config.yaml](config/config.yaml) - Configuration guide

---

**Status: ✅ Ready to Deploy**

You're all set! The agent is configured and ready to analyze your ServiceNow incidents.

Start with:
```bash
python main.py
```

Questions? Check the troubleshooting section or review the code comments.
