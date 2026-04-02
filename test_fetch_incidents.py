#!/usr/bin/env python
"""Test incident fetching"""

import sys
sys.path.insert(0, "/Users/apple/Desktop/Snow_TicketAssignment")

from dotenv import load_dotenv
import os

load_dotenv("config/.env")

from src.servicenow_client import ServiceNowClient

instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

print(f"Connecting to {instance_url}...")

client = ServiceNowClient(instance_url, username, password)

print("Fetching new incidents...")
incidents = client.get_new_incidents(limit=5)

print(f"✓ Got {len(incidents)} incidents:")
for inc in incidents:
    print(f"  - {inc['number']}: {inc['short_description'][:50]}")
