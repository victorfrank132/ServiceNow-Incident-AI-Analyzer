#!/usr/bin/env python3
"""
ServiceNow Incident AI Analyzer - Unified Startup
Single execution for webhook-based real-time incident processing
Handles ngrok tunnel, Flask server, and displays configuration
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv("config/.env")

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 80)
print("🚀 ServiceNow Incident AI Analyzer - Webhook Mode")
print("=" * 80)
print("Initialization: Loading dependencies...")

try:
    from pyngrok import ngrok
    from src.webhook_receiver import app
    print("✓ Dependencies loaded")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Configuration
FLASK_PORT = 8081  # Flask server (ngrok forwards here)
NGROK_ENABLED = False  # You're running ngrok manually
PUBLIC_URL = None
SERVER_RUNNING = True

def signal_handler(signum, frame):
    """Handle graceful shutdown."""
    global SERVER_RUNNING
    print("\n" + "=" * 80)
    print("⏹️  Received shutdown signal. Shutting down gracefully...")
    print("=" * 80)
    SERVER_RUNNING = False
    
    # Close ngrok tunnel
    try:
        ngrok.kill()
        print("✓ ngrok tunnel closed")
    except:
        pass
    
    print("✓ Server stopped")
    print("=" * 80 + "\n")
    sys.exit(0)

def setup_ngrok_tunnel():
    """Setup ngrok tunnel and get public URL."""
    global PUBLIC_URL
    
    try:
        print("🌐 Setting up ngrok tunnel...")
        # Try to connect to existing ngrok tunnel
        tunnels = ngrok.get_tunnels()
        if tunnels:
            for tunnel in tunnels:
                PUBLIC_URL = tunnel.public_url
                print(f"✓ Using existing ngrok tunnel: {PUBLIC_URL}")
                return True
        
        # Try to create new tunnel
        PUBLIC_URL = ngrok.connect(FLASK_PORT, "http")
        
        # Format the URL
        tunnel_url = str(PUBLIC_URL) if isinstance(PUBLIC_URL, str) else PUBLIC_URL
        if not tunnel_url.startswith("http"):
            tunnel_url = f"http://{tunnel_url}"
        
        PUBLIC_URL = tunnel_url
        
        print(f"✓ ngrok tunnel established: {PUBLIC_URL}")
        return True
    except Exception as e:
        print(f"⚠️  ngrok tunnel failed: {type(e).__name__}")
        if "binary was not found" in str(e):
            print("   ngrok binary not found")
            print("   Use manual setup: open another terminal and run:")
            print("   $ ngrok http 8080")
            print("   (pyngrok will auto-detect it)")
        return False

def display_startup_info():
    """Display startup information and configuration."""
    print("\n" + "=" * 80)
    print("✓ System Started Successfully")
    print("=" * 80)
    
    print("\n🚀 DEMO READY - SETUP INSTRUCTIONS:\n")
    print("   1. Flask server is running on port 8081")
    print("   2. Open ANOTHER TERMINAL and run:")
    print("")
    print("      ngrok http 8081")
    print("")
    print("   3. Copy the https:// URL from ngrok output")
    print("   4. Paste into ServiceNow webhook as:")
    print("")
    print("      https://<ngrok-url>/webhook/incident")
    print("")
    
    print("=" * 80)
    print("\n📍 LOCAL WEBHOOK ENDPOINT:\n")
    print(f"   http://localhost:{FLASK_PORT}/webhook/incident")
    
    print("\n🔗 AVAILABLE ENDPOINTS:\n")
    print(f"   GET  http://localhost:{FLASK_PORT}/ → Service info")
    print(f"   GET  http://localhost:{FLASK_PORT}/health → Health check")
    print(f"   GET  http://localhost:{FLASK_PORT}/webhook/stats → Processing stats")
    print(f"   POST http://localhost:{FLASK_PORT}/webhook/incident → Receive webhooks")
    
    print("\n🧪 TEST (without ServiceNow):\n")
    print("   python3 setup_api_incidents.py")
    print("   Creates 10 test incidents")
    
    print("\n📊 MONITORING:\n")
    print(f"   tail -f logs/webhook.log")
    
    print("\n" + "=" * 80)
    print("🎧 Listening for webhooks... (Press Ctrl+C to stop)")
    print("=" * 80 + "\n")

def main():
    """Main entry point."""
    global SERVER_RUNNING
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Display startup info
    display_startup_info()
    
    # Run Flask server
    try:
        app.run(host="127.0.0.1", port=FLASK_PORT, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
