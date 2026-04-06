# ✅ Webhook Setup Checklist

**Estimated Time:** 10-15 minutes  
**Date Completed:** _________________

---

## Prerequisites ☑️

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] ServiceNow admin access
- [ ] Terminal window ready

---

## Step 1: Install Dependencies ☑️

```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
pip install -r requirements.txt
```

**Verify:**
```bash
pip list | grep -E "flask|pyngrok|werkzeug"
```

Expected output:
```
flask              3.0.0
pyngrok            5.2.0
werkzeug           3.0.0
```

- [ ] flask installed
- [ ] pyngrok installed
- [ ] werkzeug installed

---

## Step 2: Start Webhook Server ☑️

```bash
python3 main_webhook.py
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════════════════╗
║   ServiceNow Incident AI Analyzer - Webhook Server (v2.0)           ║
║   Real-time Incident Processing via ServiceNow Webhooks             ║
╚═══════════════════════════════════════════════════════════════════════╝

✓ ngrok Tunnel Active!
═══════════════════════════════════════════════════════════════════════════
Public URL: https://stripiest-erinn-rarest.ngrok-free.dev
Local URL:  http://localhost:80
═══════════════════════════════════════════════════════════════════════════

🎧 Listening for ServiceNow webhook events...
Press Ctrl+C to stop
```

- [ ] Server started successfully
- [ ] ngrok tunnel is active
- [ ] Public URL is displayed
- [ ] "Listening for ServiceNow webhook events" message shown

**Copy your Public URL:**
```
Public URL: ____________________________________________________
```

---

## Step 3: Verify Endpoints ☑️

**In a NEW terminal window** (keep first window running):

```bash
# Health check
curl https://stripiest-erinn-rarest.ngrok-free.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T12:34:56.789012",
  "requests_processed": 0
}
```

- [ ] Health check responds
- [ ] Status is "healthy"
- [ ] Request counter shows

**Check stats:**
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats
```

Expected response:
```json
{
  "total_requests": 0,
  "cache_entries": 0,
  "timestamp": "2026-04-05T12:34:56.789012"
}
```

- [ ] Stats endpoint responds
- [ ] Request count is 0 (no webhooks processed yet)

---

## Step 4: Configure ServiceNow Webhook ☑️

### 4.1: Access ServiceNow
- [ ] Login to https://dev218421.service-now.com
- [ ] Username: ___________________ (from config/.env)
- [ ] Password: ___________________ (from config/.env)

### 4.2: Navigate to Webhooks
- [ ] Search box → Type "webhooks"
- [ ] Click: System Definition → Webhooks
- [ ] You should see existing webhooks (if any)

### 4.3: Create New Webhook
- [ ] Click **New** button
- [ ] Fill in the form:

| Field | Value |
|-------|-------|
| Name | Incident AI Analyzer |
| Table | Incident (incident) |
| Event | Insert |
| HTTP Method | POST |
| URL | `https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident` |
| Authentication | None |
| Content Type | application/json |

Checkbox options:
- [ ] Request body: (leave empty or default)
- [ ] Headers: (leave empty or default)

- [ ] Name entered
- [ ] Table set to "Incident (incident)"
- [ ] Event set to "Insert"
- [ ] HTTP Method set to "POST"
- [ ] URL set to your ngrok URL (from Step 2)
- [ ] Content Type set to "application/json"

### 4.4: Save Webhook
- [ ] Click **Save** button
- [ ] Webhook should be created successfully
- [ ] You should see it in the webhooks list

---

## Step 5: Test Real-Time Processing ☑️

### 5.1: Create Test Incident

In ServiceNow:
- [ ] Navigate to **Incidents** module
- [ ] Click **New Incident**
- [ ] Fill in the form:

| Field | Value |
|-------|-------|
| Short Description | Test API Rate Limiting |
| Description | Getting 429 Too Many Requests errors from API |
| Category | Application |
| Priority | 2 |
| Assignment Group | IT Support |

- [ ] Short description entered
- [ ] Description entered
- [ ] Click **Save**

### 5.2: Watch Webhook Process It

In your **first terminal** (running main_webhook.py):

Expected output:
```
[Webhook #1] Received incident event
Processing incident INC0010100 (event: insert)
Processing result: {...}
[✓] Webhook processing complete for INC0010100
    Confidence: 85%
    Category: Application
    Reassigned: True
```

- [ ] Webhook received the event
- [ ] Processing started immediately
- [ ] Analysis completed
- [ ] Confidence score displayed
- [ ] Category determined
- [ ] Reassignment status shown

### 5.3: Verify in ServiceNow

Go back to ServiceNow and view the incident:

- [ ] Check **Activity section** at bottom
- [ ] Look for "AI Analysis" comment
- [ ] Comment should contain:
  - Category identified
  - Confidence score
  - Root cause analysis
  - Recommended team
- [ ] Check **Assignment Group** field
  - [ ] Should be changed from "IT Support" to correct team
  - [ ] Possible teams: Infrastructure, Database, Application, Security

### 5.4: Check Statistics

In your second terminal:
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats
```

Expected response:
```json
{
  "total_requests": 1,
  "cache_entries": 1,
  "timestamp": "2026-04-05T12:34:56.789012"
}
```

- [ ] Total requests: 1 (your test incident)
- [ ] Cache entries: 1 (analysis cached)

---

## Step 6: Monitor Logs ☑️

In a third terminal:
```bash
tail -f logs/webhook.log
```

You should see entries for:
- [ ] Webhook received
- [ ] Incident processed
- [ ] Analysis results
- [ ] Comment posted
- [ ] Reassignment details

---

## Step 7: Create More Test Cases ☑️

### Test Case 1: Database Issue
- [ ] Create incident: "Connection pool exhausted"
- [ ] Category: "Application"
- [ ] Watch webhook process
- [ ] Should reassign to: **Database Team**

### Test Case 2: Infrastructure Issue
- [ ] Create incident: "Network timeout to API gateway"
- [ ] Category: "Infrastructure"
- [ ] Watch webhook process
- [ ] Should reassign to: **Infrastructure Team**

### Test Case 3: Security Issue
- [ ] Create incident: "Unauthorized access attempts"
- [ ] Category: "Security"
- [ ] Watch webhook process
- [ ] Should reassign to: **Security Team**

- [ ] Test Case 1 completed
- [ ] Test Case 2 completed
- [ ] Test Case 3 completed

---

## Step 8: Graceful Shutdown ☑️

When you're done testing:
- [ ] In first terminal: Press **Ctrl+C**
- [ ] Server should stop within 5 seconds
- [ ] ngrok tunnel should close
- [ ] Logs should show shutdown message

Expected output:
```
⏹️  Received shutdown signal. Shutting down gracefully...
✓ ngrok tunnel closed
✓ Webhook server stopped
```

---

## Troubleshooting ☑️

### Issue: Port 80 Already in Use
```bash
# Check what's using port 80
lsof -i :80

# If needed, use different port (edit main_webhook.py):
# Change: ngrok.connect(80, "http")
# To: ngrok.connect(8080, "http")
```
- [ ] Port 80 is available OR alternative port configured

### Issue: ngrok Connection Fails
```bash
# Try without auth token (free tier works)
python3 main_webhook.py

# Or sign up for ngrok and add NGROK_AUTHTOKEN to .env
```
- [ ] ngrok connection working

### Issue: ServiceNow Webhook Not Firing
- [ ] Verify webhook is enabled in ServiceNow admin
- [ ] Verify URL is correct (matches ngrok URL)
- [ ] Check ServiceNow System Log for webhook errors
- [ ] Create NEW incident (not updating existing)

- [ ] Webhook is enabled
- [ ] URL matches ngrok URL
- [ ] New incidents trigger webhook

### Issue: No Comment Posted
- [ ] Check logs: `tail -f logs/webhook.log`
- [ ] Verify confidence ≥ 70% for reassignment
- [ ] Check dedup cache: `cat logs/analyzed_incidents.json | jq .`

- [ ] Logs checked
- [ ] Confidence scores verified
- [ ] Dedup cache reviewed

---

## Final Verification ☑️

Quick final checklist:
- [ ] Dependencies installed (flask, pyngrok, werkzeug)
- [ ] Webhook server starts successfully
- [ ] ngrok tunnel is active with public URL
- [ ] Health check endpoint responds
- [ ] ServiceNow webhook created and enabled
- [ ] Test incident processed in <1 second
- [ ] Comment posted to incident
- [ ] Assignment group updated
- [ ] Logs show all events
- [ ] Graceful shutdown works (Ctrl+C)

---

## 🎉 Success!

If all checkboxes are complete, your webhook infrastructure is:
- ✅ **Installed** - All dependencies ready
- ✅ **Configured** - ServiceNow webhook setup
- ✅ **Tested** - Real-time processing verified
- ✅ **Monitored** - Logs and stats working
- ✅ **Production Ready** - Ready for live use

---

## Next Steps

1. **Production Deployment**
   - Use persistent ngrok URL (requires ngrok account)
   - Deploy to permanent server
   - Update ServiceNow webhook URL

2. **Monitoring**
   - Set up log aggregation
   - Create dashboards for webhook stats
   - Configure alerts for failures

3. **Optimization**
   - Tune LLM parameters for your use cases
   - Adjust confidence thresholds
   - Customize team routing

4. **Documentation Reference**
   - [WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md) - Detailed guide
   - [WEBHOOK_QUICK_REFERENCE.md](WEBHOOK_QUICK_REFERENCE.md) - Commands
   - [README.md](README.md) - Project overview

---

**Checklist Date:** _______________  
**Completed By:** _______________  
**Status:** ☑️ **COMPLETE**

---

**Questions?** See [WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md) for detailed troubleshooting.
