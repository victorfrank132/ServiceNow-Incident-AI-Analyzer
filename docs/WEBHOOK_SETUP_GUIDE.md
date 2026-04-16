# ServiceNow Webhook Setup Guide

**Last Updated:** April 5, 2026  
**Version:** 2.0 (Webhook-based, Real-time Processing)

---

## 🎯 Overview

This guide walks you through setting up **real-time incident processing** via ServiceNow webhooks instead of polling every 5 minutes.

**Benefits:**
- ✅ **Instant processing** - Incidents analyzed seconds after creation
- ✅ **No polling delays** - No more waiting 5 minutes
- ✅ **Public ngrok URL** - ServiceNow can reach your local machine
- ✅ **Real-time dashboard** - Monitor webhook events live
- ✅ **Production-ready** - Same quality analysis, faster response

---

## 📋 Prerequisites

### 1. Install Dependencies
```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
pip install -r requirements.txt
```

New packages added:
- `flask` - Web server for webhook endpoint
- `pyngrok` - ngrok tunneling for public URL
- `werkzeug` - WSGI utilities

### 2. ngrok Account (Optional)
- Visit https://ngrok.com
- Sign up (free tier available)
- Get your auth token
- (Not required - free tier works without auth token)

### 3. Update .env
```bash
# Optional: Add ngrok auth token for stable URLs
NGROK_AUTHTOKEN=your_ngrok_token_here
```

---

## 🚀 Quick Start

### Step 1: Start the Webhook Server
```bash
# From project directory
source .venv/bin/activate
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

### Step 2: Get Your Public URL

The script will display your ngrok public URL:
```
https://stripiest-erinn-rarest.ngrok-free.dev
```

You can also check `webhook_url.txt`:
```bash
cat webhook_url.txt
```

### Step 3: Configure ServiceNow Webhook

1. **Login to ServiceNow**
   - Instance: https://dev218421.service-now.com
   - Username/Password: from config/.env

2. **Navigate to Webhooks**
   - Search box → Type: "webhooks"
   - System Definition → Webhooks

3. **Create New Webhook**
   - Click **New**
   - Fill in the form:
     ```
     Name:           Incident AI Analyzer
     Table:          Incident (incident)
     Event:          Insert (when incident is created)
     HTTP Method:    POST
     URL:            https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident
     Authentication: None (or Basic if needed)
     Content Type:   application/json
     ```

4. **Save**

### Step 4: Test the Webhook

1. **Create a Test Incident**
   - Navigate to Incidents module
   - Create a new incident:
     ```
     Title: Test API Rate Limiting
     Description: Getting 429 Too Many Requests errors
     Category: Application
     Priority: 2
     ```

2. **Watch the Magic! 🚀**
   - In your webhook terminal, you'll see:
     ```
     [Webhook #1] Received incident event
     Processing incident INC0010100 (event: unknown)
     Processing result: {...}
     [✓] Webhook processing complete for INC0010100
         Confidence: 85%
         Category: Application
         Reassigned: True
     ```

3. **Check ServiceNow**
   - Incident should now have:
     - AI analysis comment posted
     - Assignment group updated (if confidence ≥ 70%)

---

## 📊 Monitoring

### Health Check
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T10:30:45.123456",
  "requests_processed": 5
}
```

### Stats Endpoint
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats
```

Response:
```json
{
  "total_requests": 5,
  "cache_entries": 3,
  "timestamp": "2026-04-05T10:30:45.123456"
}
```

### Real-time Logs
```bash
tail -f logs/webhook.log
```

---

## 🔄 Workflow Comparison

### Old: Polling (every 5 minutes)
```
00:00 - Check ServiceNow
00:05 - Check ServiceNow
00:10 - Check ServiceNow  ← Incident created at 00:03, processed here
✗ 7 minute delay!
```

### New: Webhooks (Real-time)
```
00:03 - Incident created in ServiceNow
00:03 - Webhook triggered immediately
00:03 - Analysis complete + Reassigned
✓ 0 second delay!
```

---

## 🔐 Security Notes

### Public URL Safety
- ngrok URL is temporary (changes on restart)
- Update webhook URL in ServiceNow if URL changes
- Use NGROK_AUTHTOKEN for persistent URLs (paid ngrok)

### Authentication
- Webhook accepts any POST (for simplicity)
- Optional: Add X-Custom-Header validation in `webhook_receiver.py`
- ServiceNow sends incident data in JSON body

### Credentials
- ServiceNow credentials only used to fetch full incident details
- Credentials stored in `config/.env` (local only)
- All API keys kept secure

---

## 🛠️ Advanced Configuration

### Custom Webhook Events

Edit `webhook_receiver.py` to handle more events:
```python
# Current: incident.create
# Add: incident.update, incident.delete, etc.
```

### Multiple Alerts

Modify `webhook_receiver.py` to send notifications:
```python
# Add Slack notification
# Add Email alert
# Add Teams message
```

### Load Balancing

For production, you can:
1. Deploy webhook server to cloud (AWS, Azure, GCP)
2. Replace ngrok with static domain
3. Use load balancer for multiple instances

---

## 🐛 Troubleshooting

### Webhook Not Triggering

**Problem:** ServiceNow webhooks not firing  
**Solution:**
1. Check webhook is enabled in ServiceNow
2. Check URL is correct in webhook config
3. Create new incident (not update existing)
4. Check ServiceNow logs: System Log → Webhooks

### ngrok Connection Failed

**Problem:** `error: Connection refused`  
**Solution:**
```bash
# Make sure Flask is listening on port 80
# On macOS, you may need sudo:
sudo python3 main_webhook.py

# Or use different port:
# Edit main_webhook.py: port=8080
# Edit ngrok: ngrok.connect(8080, "http")
```

### Public URL Keeps Changing

**Problem:** New ngrok URL on each restart  
**Solution:**
1. Sign up for ngrok account
2. Add NGROK_AUTHTOKEN to .env:
   ```
   NGROK_AUTHTOKEN=your_token_here
   ```
3. Restart webhook server
4. URL will be persistent

### ServiceNow API Authentication

**Problem:** `Authentication failed`  
**Solution:**
1. Verify SERVICENOW_USERNAME and PASSWORD in config/.env
2. Verify instance URL: https://dev218421.service-now.com
3. Try API call manually:
   ```bash
   curl -u admin:password \
     https://dev218421.service-now.com/api/now/v2/table/incident?limit=1
   ```

---

## 📝 API Endpoints

### GET /health
Health check endpoint
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/health
```

### GET /webhook/stats
Processing statistics
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats
```

### POST /webhook/incident
Receive incident events (ServiceNow sends here)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"number":"INC0010100","short_description":"Test"}' \
  https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident
```

### GET /
Root endpoint - usage information
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/
```

---

## 📈 Performance Metrics

- **Webhook latency:** <1 second (local processing)
- **LLM analysis time:** 30-60 seconds (NVIDIA GPT-OSS-120B)
- **Total processing time:** 30-61 seconds from incident creation to reassignment
- **Throughput:** 1 incident per 30-60 seconds (depends on LLM response time)

---

## 🔄 Comparison: Polling vs Webhooks

| Feature | Polling | Webhooks |
|---------|---------|----------|
| **Trigger** | Timer (5 min) | Event (instant) |
| **Latency** | 0-5 minutes | <1 second |
| **API Calls** | Constant (~30/day) | Only on event |
| **Server Load** | High (always checking) | Low (event-driven) |
| **Setup** | Simple | Requires ngrok/tunnel |
| **Real-time** | No | Yes ✓ |
| **Production Ready** | Yes | Yes ✓ |

---

## 🚀 Next Steps

1. ✅ Start webhook server: `python3 main_webhook.py`
2. ✅ Get public URL from ngrok output
3. ✅ Configure ServiceNow webhook with URL
4. ✅ Create test incident and watch it process instantly
5. ✅ Monitor logs and stats in real-time

---

## 📞 Support

For issues:
1. Check logs: `tail -f logs/webhook.log`
2. Check stats: `curl {ngrok-url}/webhook/stats`
3. Check health: `curl {ngrok-url}/health`
4. Review webhook config in ServiceNow
5. Check ServiceNow System Log for webhook errors

---

**Version:** 2.0 Webhook-based  
**Status:** Production Ready  
**Last Update:** April 5, 2026
