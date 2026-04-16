#!/usr/bin/env python
"""Debug script to test ServiceNow incident queries."""

import os
import sys
from dotenv import load_dotenv

load_dotenv("config/.env")
sys.path.insert(0, os.path.dirname(__file__))

from src.servicenow_client import ServiceNowClient

client = ServiceNowClient(
    instance_url=os.getenv("SERVICENOW_INSTANCE_URL"),
    username=os.getenv("SERVICENOW_USERNAME"),
    password=os.getenv("SERVICENOW_PASSWORD")
)

print("=== Test 1: Query with state IN (1,2) ===")
query_params = {
    'sysparm_query': 'state IN (1,2)^ORDERBYDESCsys_created_on',
    'sysparm_limit': 10,
    'sysparm_fields': 'sys_id,number,short_description,state'
}

response = client.session.get(
    f'{client.api_url}/table/incident',
    headers=client._get_headers(),
    params=query_params,
    timeout=client.timeout
)

print(f'Status: {response.status_code}')
result = response.json()
incidents = result.get('result', [])
print(f'Total returned: {len(incidents)}')
for inc in incidents:
    print(f"  - {inc.get('number')}: state={inc.get('state')}")

print("\n=== Test 2: Query all incidents (no state filter) ===")
query_params2 = {
    'sysparm_query': 'ORDERBYDESCsys_created_on',
    'sysparm_limit': 10,
    'sysparm_fields': 'sys_id,number,short_description,state'
}

response2 = client.session.get(
    f'{client.api_url}/table/incident',
    headers=client._get_headers(),
    params=query_params2,
    timeout=client.timeout
)

print(f'Status: {response2.status_code}')
result2 = response2.json()
incidents2 = result2.get('result', [])
print(f'Total returned: {len(incidents2)}')
for inc in incidents2:
    print(f"  - {inc.get('number')}: state={inc.get('state')}")

print("\n=== Test 3: Query with state=1 only ===")
query_params3 = {
    'sysparm_query': 'state=1^ORDERBYDESCsys_created_on',
    'sysparm_limit': 10,
    'sysparm_fields': 'sys_id,number,short_description,state'
}

response3 = client.session.get(
    f'{client.api_url}/table/incident',
    headers=client._get_headers(),
    params=query_params3,
    timeout=client.timeout
)

print(f'Status: {response3.status_code}')
result3 = response3.json()
incidents3 = result3.get('result', [])
print(f'Total returned: {len(incidents3)}')
for inc in incidents3:
    print(f"  - {inc.get('number')}: state={inc.get('state')}")
