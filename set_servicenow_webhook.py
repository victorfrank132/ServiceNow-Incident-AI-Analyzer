#!/usr/bin/env python3
"""Create or update the ServiceNow webhook system property."""

import os
import sys
from dotenv import load_dotenv

from src.servicenow_client import ServiceNowClient


PROPERTY_NAME = "x_servicenow_incident_analyzer.webhook_url"
PROPERTY_DESCRIPTION = "Public webhook URL for the ServiceNow Incident AI Analyzer."


def main() -> int:
    """Set the webhook property in the configured ServiceNow instance."""
    load_dotenv("config/.env")

    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <webhook-url>")
        return 1

    webhook_url = sys.argv[1].strip()
    if not webhook_url.startswith(("http://", "https://")):
        print("Webhook URL must start with http:// or https://")
        return 1

    client = ServiceNowClient(
        instance_url=os.getenv("SERVICENOW_INSTANCE_URL", ""),
        username=os.getenv("SERVICENOW_USERNAME"),
        password=os.getenv("SERVICENOW_PASSWORD"),
    )

    if not client.instance_url or not client.username or not client.password:
        print("Missing ServiceNow credentials in config/.env")
        return 1

    updated_property = client.set_system_property(
        property_name=PROPERTY_NAME,
        value=webhook_url,
        description=PROPERTY_DESCRIPTION,
    )

    if not updated_property:
        print(f"Failed to update {PROPERTY_NAME}")
        return 1

    confirmed_property = client.get_system_property(PROPERTY_NAME)
    if not confirmed_property:
        print(f"Updated {PROPERTY_NAME}, but could not re-read it for verification")
        return 1

    print(f"Property: {confirmed_property.get('name')}")
    print(f"Value: {confirmed_property.get('value')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
