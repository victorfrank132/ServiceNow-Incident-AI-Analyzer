#!/bin/bash
# Quick start script for ServiceNow Incident AI Analyzer - Webhook Mode

cd "$(dirname "$0")" || exit 1

echo "🚀 Starting ServiceNow Incident AI Analyzer..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check dependencies
echo "✓ Environment activated"

# Run the startup script
echo ""
python3 start.py
