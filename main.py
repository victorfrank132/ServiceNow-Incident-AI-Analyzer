"""Main entry point for the ServiceNow incident analysis agent."""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.servicenow_client import ServiceNowClient
from src.incident_analyzer import IncidentAnalyzer
from src.incident_processor import IncidentProcessor
from src.logging import setup_logging
from src.utils import load_config, load_team_mappings, validate_config, ensure_directories_exist

# Load environment variables from config/.env
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

# Setup logging
logger = setup_logging(log_level="INFO", log_file="logs/incident_agent.log")

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
    logger.info("⛔ Shutdown signal received - stopping gracefully...")
    if signum == signal.SIGTERM:
        logger.warning("⊠ Forced termination signal (SIGTERM) - may not complete current operation")


def main():
    """Main entry point for the incident agent."""
    global shutdown_requested
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        logger.info("Starting ServiceNow Incident Analysis Agent")

        # Ensure required directories exist
        ensure_directories_exist(["logs", "config"])

        # Load configuration
        config = load_config("config/config.yaml")
        if not validate_config(config):
            logger.error("Invalid configuration")
            sys.exit(1)

        # Load team mappings
        team_mappings = load_team_mappings("config/team_mappings.json")
        logger.info(f"Loaded team mappings: {len(team_mappings)} categories")

        # Get credentials from environment
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
        auth_type = config.get("servicenow", {}).get("auth_type", "basic")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")

        # Get auth credentials based on auth type
        if auth_type == "basic":
            username = os.getenv("SERVICENOW_USERNAME")
            password = os.getenv("SERVICENOW_PASSWORD")
            if not all([instance_url, username, password, nvidia_api_key]):
                logger.error("Missing required environment variables. Check config/.env file")
                logger.error("Required: SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD, NVIDIA_API_KEY")
                sys.exit(1)
            logger.info(f"Connecting to ServiceNow instance: {instance_url} (basic auth)")
            snow_client = ServiceNowClient(
                instance_url=instance_url,
                username=username,
                password=password,
                auth_type="basic"
            )
        else:  # oauth
            client_id = os.getenv("SERVICENOW_CLIENT_ID")
            client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
            if not all([instance_url, client_id, client_secret, nvidia_api_key]):
                logger.error("Missing required environment variables. Check config/.env file")
                logger.error("Required: SERVICENOW_INSTANCE_URL, SERVICENOW_CLIENT_ID, SERVICENOW_CLIENT_SECRET, NVIDIA_API_KEY")
                sys.exit(1)
            logger.info(f"Connecting to ServiceNow instance: {instance_url} (OAuth)")
            snow_client = ServiceNowClient(
                instance_url=instance_url,
                client_id=client_id,
                client_secret=client_secret,
                auth_type="oauth"
            )

        # Initialize LLM analyzer
        logger.info("Initializing LLM analyzer with NVIDIA GPT-OSS-120B (with reasoning)")
        analyzer = IncidentAnalyzer(
            openai_api_key=None,
            team_mappings=team_mappings,
            nvidia_api_key=nvidia_api_key
        )

        # Initialize processor
        incident_config = config.get("incident_processing", {})
        processor = IncidentProcessor(
            servicenow_client=snow_client,
            analyzer=analyzer,
            auto_reassign=config.get("analysis", {}).get("auto_reassign", True),
            auto_close=config.get("analysis", {}).get("auto_close", True),
            rate_limit_delay=incident_config.get("rate_limit_delay_seconds", 1)
        )

        # Main processing loop
        polling_interval = config.get("servicenow", {}).get("polling_interval_seconds", 300)
        max_incidents = incident_config.get("max_incidents_per_run", 10)

        logger.info(f"Starting polling loop (interval: {polling_interval}s, max incidents: {max_incidents})")

        run_count = 0
        while True:
            try:
                run_count += 1
                logger.info(f"=== Processing run #{run_count} ===")

                # Process incidents
                if shutdown_requested:
                    logger.info("Shutdown requested - stopping")
                    break
                    
                results = processor.process_incidents(max_incidents=max_incidents)

                # Log summary
                summary = processor.get_processing_summary(results)
                logger.info(f"\n{summary}")

                # Wait for next polling interval with interruptible sleep
                if not shutdown_requested:
                    logger.info(f"Waiting {polling_interval} seconds for next run... (Press Ctrl+C to stop)")
                    # Break sleep into smaller chunks so Ctrl+C is responsive
                    sleep_chunk = min(5, polling_interval)
                    remaining = polling_interval
                    while remaining > 0 and not shutdown_requested:
                        sleep_duration = min(sleep_chunk, remaining)
                        time.sleep(sleep_duration)
                        remaining -= sleep_duration

            except KeyboardInterrupt:
                logger.info("⛔ Interrupted by user (Ctrl+C)")
                shutdown_requested = True
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                if not shutdown_requested:
                    logger.info("Retrying in 30 seconds...")
                    time.sleep(min(30, polling_interval))

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    
    logger.info("✅ Agent shutting down gracefully")
    sys.exit(0)


if __name__ == "__main__":
    main()
