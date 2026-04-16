# 🚀 START WEBHOOK NOW (2 Minutes)

**Want to start webhooks immediately?** Follow this quick guide.

---

## Terminal 1: Install & Start

```bash
cd /Users/apple/Desktop/Snow_TicketAssignment
source .venv/bin/activate
pip install -r requirements.txt
python3 main_webhook.py
```

**You'll see:**
```
Public URL: https://stripiest-erinn-rarest.ngrok-free.dev
🎧 Listening for ServiceNow webhook events...
```

📌 **Copy the URL shown above** (it's your public webhook URL)

---

## Terminal 2: In ServiceNow (While Terminal 1 Runs)

1. Go to: https://dev218421.service-now.com
2. Search → "webhooks"
3. Click: **System Definition → Webhooks**
4. New Webhook with these values:

| Field | Value |
|-------|-------|
| Name | Incident AI Analyzer |
| Table | Incident (incident) |
| Event | Insert |
| HTTP Method | POST |
| URL | ` https://stripiest-erinn-rarest.ngrok-free.dev/webhook/incident` |
| Content Type | application/json |

Click **Save**

---

## Terminal 2: Test It

```bash
# Check it's working
curl https://stripiest-erinn-rarest.ngrok-free.dev/health
```

Should respond:
```json
{"status": "healthy", "timestamp": "...", "requests_processed": 0}
```

✅ **Ready!**

---

## Test: Create Incident in ServiceNow

1. **Incidents** module
2. **New Incident**
3. Title: `Test API Error`
4. Description: `Getting timeout errors`
5. **Save**

---

## Watch Terminal 1

You should see:
```
[Webhook #1] Received incident event
Processing incident INC0010100
[✓] Webhook processing complete
    Confidence: 85%
    Category: Application
    Reassigned: True
```

**Check ServiceNow incident:**
- ✅ AI analysis comment posted
- ✅ Assignment group updated

---

## Done! 🎉

Your webhooks are live and processing incidents **instantly**.

### Next Steps

1. Create more incidents to test
2. Monitor live: `tail -f logs/webhook.log`
3. Check stats: `curl {your-url}/webhook/stats`
4. For details: See [WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md)

### Stop Server
```bash
# In Terminal 1, press: Ctrl+C
```

---

**More info:** [WEBHOOK_QUICK_REFERENCE.md](WEBHOOK_QUICK_REFERENCE.md)  
**Detailed setup:** [WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md)  
**Full checklist:** [WEBHOOK_SETUP_CHECKLIST.md](WEBHOOK_SETUP_CHECKLIST.md)
