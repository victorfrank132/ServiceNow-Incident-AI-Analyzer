# 🚀 Manual ngrok Setup Guide

**Status:** Updated for manual ngrok on port 80

---

## Quick Start (2 Steps)

### Terminal 1: Start Flask Webhook Server
```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate

# Run with sudo (port 80 requires root)
sudo python3 main_webhook.py
```

**Output:**
```
✓ Flask server listening on: http://localhost:80
✓ Waiting for ServiceNow webhook events...

💡 MAKE SURE NGROK IS RUNNING...
```

### Terminal 2: Start ngrok Tunnel
```bash
# Open another terminal and run:
ngrok http 80

# Or with permanent URL (requires auth token):
ngrok http 80 --authtoken YOUR_NGROK_TOKEN
```

**Output:**
```
ngrok  by @inconshreveable                                    (Ctrl+C to quit)

Session Status            online
Account                   your-account
Version                   3.x.x
Region                    us (United States)
Latency                   -
Web Interface             http://127.0.0.1:4040
Forwarding                https://abc123def456.ngrok-free.dev -> http://localhost:80

Connections               ttl    opn    rt1    rt5    p50    p95
                          0      0      0.00   0.00   0.00   0.00
```

---

## 📌 Copy Your Public URL

From ngrok output, your public URL is:
```
https://abc123def456.ngrok-free.dev
```

---

## ⚙️ Configure ServiceNow Webhook

1. **Login to ServiceNow:**
   - https://dev218421.service-now.com

2. **Navigate to Webhooks:**
   - Search box → "webhooks"
   - System Definition → Webhooks

3. **Create New Webhook:**
   ```
   Name:           Incident AI Analyzer
   Table:          Incident (incident)
   Event:          Insert
   HTTP Method:    POST
   URL:            https://abc123def456.ngrok-free.dev/webhook/incident
   Content Type:   application/json
   ```
   (Replace `abc123def456` with your actual ngrok subdomain)

4. **Save**

---

## ✅ Test It

### Create Test Incident
1. Go to Incidents module in ServiceNow
2. Create new incident:
   ```
   Title: Test Webhook
   Description: Testing webhook integration
   Category: Applications
   ```
3. Save

### Watch Flask Terminal
You should see:
```
[Webhook #1] Received incident event
Processing incident INC0010XXX
[✓] Webhook processing complete
```

### Watch Logs
```bash
tail -f logs/webhook.log
```

---

## 🔗 API Endpoints

While webhook server is running on port 80:

```bash
# Health check
curl http://localhost:80/health

# Stats
curl http://localhost:80/webhook/stats

# Root info
curl http://localhost:80/
```

---

## 🔄 ngrok URL Changes

⚠️ **Important:** Free ngrok URLs change every ~2 hours.

**If URL changes:**
1. Stop ngrok (Ctrl+C)
2. Restart ngrok: `ngrok http 80`
3. Copy new URL
4. Update ServiceNow webhook with new URL

**Solution: Get Permanent URL**
- Sign up at https://ngrok.com
- Get auth token
- Run: `ngrok http 80 --authtoken YOUR_TOKEN`
- URL stays the same across restarts

---

## 🛠️ Troubleshooting

### Port 80 Permission Denied
```bash
# Solution 1: Use sudo
sudo python3 main_webhook.py

# Solution 2: Use different port (8080)
# Edit main_webhook.py, change port 80 to 8080
# Also update ngrok: ngrok http 8080
```

### ngrok Not Connecting
```bash
# Make sure ngrok is running
ngrok http 80

# Verify Flask is accessible
curl http://localhost:80/health
```

### ServiceNow Webhook Not Firing
1. Check webhook is enabled in ServiceNow
2. Verify URL is correct (from ngrok)
3. Check ServiceNow System Log for errors
4. Create NEW incident (not updating existing)

---

## 📊 Typical Workflow

```
ServiceNow Incident Created
    ↓
ngrok tunnel receives (instant)
    ↓
Flask app processes (http://localhost:80)
    ↓
LLM analyzes (30-60 seconds)
    ↓
Comment posted to incident
    ↓
Assignment updated (if confidence ≥ 70%)
```

---

## 💾 Files to Know

| File | Purpose |
|------|---------|
| `main_webhook.py` | Flask server entry point |
| `src/webhook_receiver.py` | Webhook handler |
| `logs/webhook.log` | Processing logs |
| `config/.env` | Credentials |

---

## 🎯 Summary

✅ **You're all set for manual ngrok mode!**

1. Start Flask: `sudo python3 main_webhook.py` (Terminal 1)
2. Start ngrok: `ngrok http 80` (Terminal 2)
3. Copy ngrok URL → Configure in ServiceNow
4. Create incident → Watch it process instantly!

---

**Created:** April 6, 2026  
**Mode:** Manual ngrok (Port 80)  
**Status:** ✅ Ready to Use
