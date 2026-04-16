"""Enhanced test script to explore ServiceNow incidents and assignment groups."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.servicenow_client import ServiceNowClient
from src.utils import load_config

def explore_incidents():
    """Explore incidents in ServiceNow to understand available data."""
    print("=" * 70)
    print("ServiceNow Incident Explorer")
    print("=" * 70)
    
    # Load config
    config = load_config("config/config.yaml")
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    auth_type = config.get("servicenow", {}).get("auth_type", "basic")
    
    # Initialize client
    if auth_type == "basic":
        username = os.getenv("SERVICENOW_USERNAME")
        password = os.getenv("SERVICENOW_PASSWORD")
        client = ServiceNowClient(
            instance_url=instance_url,
            username=username,
            password=password,
            auth_type="basic"
        )
    else:
        client_id = os.getenv("SERVICENOW_CLIENT_ID")
        client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
        client = ServiceNowClient(
            instance_url=instance_url,
            client_id=client_id,
            client_secret=client_secret,
            auth_type="oauth"
        )
    
    print(f"\n📋 Connected to: {instance_url}\n")
    
    # Test 1: Show incidents in New/In Progress state
    print("=" * 70)
    print("Test 1: Incidents in New or In Progress state (state IN 1,2)")
    print("=" * 70)
    
    try:
        incidents = client.get_new_incidents(state=["1", "2"], limit=10)
        if incidents:
            print(f"\n✅ Found {len(incidents)} incidents:\n")
            for i, incident in enumerate(incidents, 1):
                print(f"  {i}. [{incident.get('number', 'N/A')}] {incident.get('short_description', 'N/A')}")
                print(f"     State: {incident.get('state', 'N/A')}, Category: {incident.get('category', 'N/A')}")
                print(f"     Assigned to: {incident.get('assigned_to', 'UNASSIGNED')}")
        else:
            print("\n⚠️  No incidents found in New or In Progress state")
            print("    This is normal if all incidents are assigned or resolved")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    # Test 2: Show all incidents (any state)
    print("\n" + "=" * 70)
    print("Test 2: All incidents (any state, recent first)")
    print("=" * 70)
    
    try:
        # Query all incidents sorted by creation date
        response = client.session.get(
            f"{client.api_url}/table/incident",
            headers=client._get_headers(),
            params={
                "sysparm_query": "ORDERBYDESCsys_created_on",
                "sysparm_limit": 5,
                "sysparm_fields": "sys_id,number,short_description,state,assigned_to,assignment_group,category"
            },
            timeout=client.timeout
        )
        
        if response.status_code == 200:
            all_incidents = response.json().get("result", [])
            if all_incidents:
                print(f"\n✅ Found {len(all_incidents)} recent incidents:\n")
                for i, incident in enumerate(all_incidents, 1):
                    state_map = {"1": "New", "2": "In Progress", "3": "On Hold", "6": "Resolved", "7": "Closed"}
                    state_name = state_map.get(incident.get('state', ''), incident.get('state', 'Unknown'))
                    print(f"  {i}. [{incident.get('number', 'N/A')}] {incident.get('short_description', 'N/A')}")
                    print(f"     State: {state_name} ({incident.get('state', 'N/A')})")
                    print(f"     Category: {incident.get('category', 'N/A')}")
                    print(f"     Assignment Group: {incident.get('assignment_group', 'NONE')}")
            else:
                print("\n⚠️  No incidents found")
        else:
            print(f"\n❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    # Test 3: Show assignment groups
    print("\n" + "=" * 70)
    print("Test 3: Available Assignment Groups")
    print("=" * 70)
    
    try:
        response = client.session.get(
            f"{client.api_url}/table/sys_user_group",
            headers=client._get_headers(),
            params={
                "sysparm_limit": 20,
                "sysparm_fields": "sys_id,name"
            },
            timeout=client.timeout
        )
        
        if response.status_code == 200:
            groups = response.json().get("result", [])
            if groups:
                print(f"\n✅ Found {len(groups)} assignment groups:\n")
                for i, group in enumerate(groups, 1):
                    print(f"  {i}. {group.get('name', 'UNKNOWN')} (ID: {group.get('sys_id', 'N/A')})")
            else:
                print("\n⚠️  No assignment groups found")
        else:
            print(f"\n❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    # Test 4: Show incident categories
    print("\n" + "=" * 70)
    print("Test 4: Common Incident Categories")
    print("=" * 70)
    
    try:
        response = client.session.get(
            f"{client.api_url}/table/incident",
            headers=client._get_headers(),
            params={
                "sysparm_query": "categoryISNOTEMPTY",
                "sysparm_limit": 10,
                "sysparm_fields": "category",
                "sysparm_distinct": "true"
            },
            timeout=client.timeout
        )
        
        if response.status_code == 200:
            incidents = response.json().get("result", [])
            categories = set()
            for incident in incidents:
                if incident.get('category'):
                    categories.add(incident.get('category'))
            
            if categories:
                print(f"\n✅ Found {len(list(categories))} incident categories in use:\n")
                for i, cat in enumerate(sorted(categories), 1):
                    print(f"  {i}. {cat}")
            else:
                print("\n⚠️  No categories found")
        else:
            print(f"\n⚠️  Could not fetch categories (API returned {response.status_code})")
    except Exception as e:
        print(f"\n⚠️  Error fetching categories: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Exploration Complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        explore_incidents()
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
