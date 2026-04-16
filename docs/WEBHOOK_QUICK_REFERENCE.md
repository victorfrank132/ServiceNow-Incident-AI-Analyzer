# 🚀 Webhook Quick Reference Card

## Step 1: Start the Server
```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
python3 main_webhook.py
```

---

## Step 2: Copy Your Public URL

When you run the command above, you'll see output like:
```
Public URL: https://stripiest-erinn-rarest.ngrok-free.dev
```

Or find it here:
```bash
cat webhook_url.txt
```

---

## Step 3: Configure ServiceNow Webhook

**In ServiceNow Admin (https://dev218421.service-now.com):**

1. Search → **Webhooks**
2. New Webhook:
   - **Name:** Incident AI Analyzer
   - **Table:** Incident (incident)
   - **Event:** Insert
   - **HTTP Method:** POST
   - **URL:** `https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident`
   - **Content Type:** application/json
3. Save

---

## Step 4: Test It!

### Test in Terminal
```bash
# Check health
curl https://stripiest-erinn-rarest.ngrok-free.dev/health

# Check stats
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats

# View root info
curl https://stripiest-erinn-rarest.ngrok-free.dev/
```

### Test in ServiceNow
1. Create new incident
2. Watch your webhook terminal
3. Check incident for posted comment
4. Check assignment group (updated if confidence ≥ 70%)

---

## 📍 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/webhook/incident` | POST | Receive incidents |
| `/webhook/stats` | GET | Statistics |

---

## 📋 Common cURL Commands

### Health Check
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/health | jq .
```

### Check Stats
```bash
curl https://stripiest-erinn-rarest.ngrok-free.dev/webhook/stats | jq .
```

### Test Webhook Manually
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"number":"INC0010100"}' \
  https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident | jq .
```

### Watch Logs
```bash
tail -f logs/webhook.log
```

---

## 🎯 Expected Workflow

```
1. Create incident in ServiceNow
   ↓
2. ServiceNow fires webhook event
   ↓
3. ngrok receives event at public URL
   ↓
4. Flask webhook handler processes
   ↓
5. AI Analyzer runs NVIDIA LLM (30-60s)
   ↓
6. Posts comment to incident
   ↓
7. Updates assignment group (if confidence ≥ 70%)
   ↓
8. Logs event to webhook.log
```

---

## 🔧 Troubleshooting Quick Links

- Full Guide: [WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md)
- Main Script: [main_webhook.py](main_webhook.py)
- Receiver Code: [src/webhook_receiver.py](src/webhook_receiver.py)
- Config: [config/.env](config/.env)
- Logs: [logs/webhook.log](logs/webhook.log)

---

## 🛑 Stop the Server

Press **Ctrl+C** in the terminal running `python3 main_webhook.py`

---

## 💡 Pro Tips

1. **Keep terminal window open** - Server exits when terminal closes
2. **Monitor logs in another terminal** - `tail -f logs/webhook.log`
3. **Check stats regularly** - `curl {url}/webhook/stats`
4. **Save your public URL** - It's in `webhook_url.txt`
5. **Update ServiceNow webhook if URL changes** - Create new webhook config

---

**Last Updated:** April 5, 2026  
**Status:** ✅ Ready to Use
