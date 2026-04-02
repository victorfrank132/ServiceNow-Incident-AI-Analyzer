"""Test script to verify ServiceNow connection and incident fetching."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.servicenow_client import ServiceNowClient
from src.utils import load_config

def test_connection():
    """Test conexión to ServiceNow instance."""
    print("=" * 60)
    print("ServiceNow Connection Test")
    print("=" * 60)
    
    # Load config
    config = load_config("config/config.yaml")
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    auth_type = config.get("servicenow", {}).get("auth_type", "basic")
    
    print(f"\nInstance URL: {instance_url}")
    print(f"Auth Type: {auth_type}")
    
    # Initialize client
    if auth_type == "basic":
        username = os.getenv("SERVICENOW_USERNAME")
        password = os.getenv("SERVICENOW_PASSWORD")
        
        if not username or not password:
            print("❌ ERROR: Missing username/password in config/.env")
            return False
        
        print(f"Username: {username}")
        
        client = ServiceNowClient(
            instance_url=instance_url,
            username=username,
            password=password,
            auth_type="basic"
        )
    else:
        client_id = os.getenv("SERVICENOW_CLIENT_ID")
        client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("❌ ERROR: Missing client_id/client_secret in config/.env")
            return False
        
        client = ServiceNowClient(
            instance_url=instance_url,
            client_id=client_id,
            client_secret=client_secret,
            auth_type="oauth"
        )
    
    # Test fetching incidents
    print("\n" + "-" * 60)
    print("Testing: Fetch open incidents...")
    print("-" * 60)
    
    try:
        incidents = client.get_new_incidents(limit=5)
        
        if incidents:
            print(f"✅ SUCCESS: Found {len(incidents)} open incidents\n")
            for i, incident in enumerate(incidents, 1):
                print(f"  {i}. {incident.get('number', 'N/A')} - {incident.get('short_description', 'N/A')}")
            return True
        else:
            print("⚠️  WARNING: No open incidents found (this is normal if there are none)")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch incidents: {str(e)}")
        print("\nTroubleshooting tips:")
        print("  - Check SERVICENOW_INSTANCE_URL is correct")
        print("  - Check SERVICENOW_USERNAME and SERVICENOW_PASSWORD are correct")
        print("  - Verify the user account can access the ServiceNow REST API")
        print("  - Check network connectivity to the ServiceNow instance")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
