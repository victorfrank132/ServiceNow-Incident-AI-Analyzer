#!/bin/bash
# Quick startup script for ServiceNow Incident AI Analyzer

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 ServiceNow Incident AI Analyzer - Startup Guide"
echo "════════════════════════════════════════════════════════════════"
echo ""

PROJECT_DIR="/Users/apple/Desktop/Snow_TicketAssignment"

# Check if .env has OpenAI API key
if ! grep -q "OPENAI_API_KEY=sk-" "$PROJECT_DIR/config/.env" 2>/dev/null; then
    echo "⚠️  WARNING: OpenAI API key not configured!"
    echo ""
    echo "Steps to configure:"
    echo "  1. Get your API key from: https://platform.openai.com/account/api-keys"
    echo "  2. Edit: config/.env"
    echo "  3. Set:  OPENAI_API_KEY=sk-your-key-here"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Test ServiceNow connection first
echo "🔍 Testing ServiceNow connection..."
echo ""
cd "$PROJECT_DIR"
source .venv/bin/activate 2>/dev/null

python test_connection.py
TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -ne 0 ]; then
    echo "❌ Connection test failed!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Connection verified! Ready to start the agent."
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Starting incident analysis loop..."
echo "  • Polling interval: 5 minutes"
echo "  • Max incidents per cycle: 10"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "Logs: tail -f logs/incident_agent.log"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Start the agent
python main.py
