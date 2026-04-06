#!/usr/bin/env python3
"""
Webhook receiver for real-time incident processing via ServiceNow webhooks.
Listens for incident.create events and processes them immediately.
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.servicenow_client import ServiceNowClient
from src.incident_analyzer import IncidentAnalyzer
from src.incident_processor import IncidentProcessor
from src.splunk_client import build_splunk_client_from_env
from src.logging import setup_logging
from src.utils import load_config, load_team_mappings

# Setup
load_dotenv("config/.env")
logger = setup_logging("INFO", "logs/webhook.log")
config = load_config("config/config.yaml")

# Initialize clients
snow_client = ServiceNowClient(
    instance_url=os.getenv("SERVICENOW_INSTANCE_URL"),
    username=os.getenv("SERVICENOW_USERNAME"),
    password=os.getenv("SERVICENOW_PASSWORD")
)

# Load team mappings
try:
    team_mappings = load_team_mappings("config/team_mappings.json")
except:
    team_mappings = {}
    logger.warning("Could not load team_mappings.json - using empty mappings")

# Initialize analyzer
analyzer = IncidentAnalyzer(
    openai_api_key=None,
    team_mappings=team_mappings,
    nvidia_api_key=os.getenv("NVIDIA_API_KEY")
)

splunk_client = build_splunk_client_from_env(config.get("splunk", {}))

# Initialize processor
processor = IncidentProcessor(
    servicenow_client=snow_client,
    analyzer=analyzer,
    splunk_client=splunk_client,
    auto_reassign=True
)

# Flask app
app = Flask(__name__)

# Request counter
request_count = 0


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for ngrok."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "requests_processed": request_count
    }), 200


@app.route("/webhook/incident", methods=["POST"])
def incident_webhook():
    """
    Webhook endpoint for ServiceNow incident events.
    ServiceNow sends POST requests here when incidents are created/updated.
    """
    global request_count
    request_count += 1
    
    try:
        # Get webhook payload
        data = request.get_json()
        
        if not data:
            logger.warning("Received empty webhook payload")
            return jsonify({"error": "Empty payload"}), 400
        
        logger.info(f"[Webhook #{request_count}] Received incident event")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        # Extract incident data
        incident_number = data.get("number") or data.get("sys_id")
        event_type = data.get("event") or "unknown"
        
        if not incident_number:
            logger.warning("No incident number in webhook payload")
            return jsonify({"error": "Missing incident number"}), 400
        
        logger.info(f"Processing incident {incident_number} (event: {event_type})")
        
        # If this is an incident object, process directly
        if "short_description" in data or "description" in data:
            # Direct incident data from webhook
            result = processor.process_single_incident(data)
            logger.info(f"Processing result: {result}")
            
            return jsonify({
                "status": "processed",
                "incident": incident_number,
                "result": result
            }), 200
        
        # Otherwise, fetch the incident from ServiceNow
        logger.info(f"Fetching full incident details for {incident_number}")
        incident = snow_client.get_incident_details(incident_number)
        
        if not incident:
            logger.warning(f"Could not find incident {incident_number}")
            return jsonify({"error": "Incident not found"}), 404
        logger.info(f"Fetched incident {incident_number}, processing...")
        
        # Process the incident
        result = processor.process_single_incident(incident)
        analysis = result.get("analysis") or {}
        
        logger.info(f"[✓] Webhook processing complete for {incident_number}")
        logger.info(f"    Confidence: {analysis.get('confidence', 'N/A')}%")
        logger.info(f"    Category: {analysis.get('category', 'N/A')}")
        logger.info(f"    Reassigned: {result.get('reassigned', False)}")
        
        return jsonify({
            "status": "processed",
            "incident": incident_number,
            "success": result.get("success", False),
            "confidence": analysis.get("confidence"),
            "category": analysis.get("category"),
            "reassigned": result.get("reassigned")
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500


@app.route("/webhook/stats", methods=["GET"])
def webhook_stats():
    """Return webhook processing statistics."""
    return jsonify({
        "total_requests": request_count,
        "cache_entries": len(processor.analyzed_incidents),
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint - usage information."""
    return jsonify({
        "service": "ServiceNow Incident AI Analyzer - Webhook Receiver",
        "version": "2.0 (webhook-based)",
        "endpoints": {
            "/health": "Health check",
            "/webhook/incident": "POST - Receive incident events",
            "/webhook/stats": "Webhook statistics",
            "/": "This page"
        },
        "instructions": "Configure ServiceNow webhook to POST to: https://yourngrok.url/webhook/incident"
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    default_port = int(os.getenv("WEBHOOK_PORT", "8081"))
    logger.info("=" * 70)
    logger.info("ServiceNow Incident AI Analyzer - Webhook Server")
    logger.info("=" * 70)
    logger.info(f"Starting webhook server on http://localhost:{default_port}")
    logger.info(f"Endpoints:")
    logger.info(f"  - Health: http://localhost:{default_port}/health")
    logger.info(f"  - Webhook: http://localhost:{default_port}/webhook/incident")
    logger.info(f"  - Stats: http://localhost:{default_port}/webhook/stats")
    logger.info("=" * 70)
    logger.info("Waiting for ServiceNow webhook events...")
    logger.info("=" * 70)
    
    # Run Flask app
    app.run(
        host="0.0.0.0",
        port=default_port,
        debug=False,
        use_reloader=False
    )
