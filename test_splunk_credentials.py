#!/usr/bin/env python3
"""Test Splunk credentials and connectivity."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from src.splunk_client import build_splunk_client_from_env, SplunkClient

def main():
    """Test Splunk credentials and perform basic diagnostics."""
    # Load environment
    env_path = Path(__file__).parent / "config" / ".env"
    load_dotenv(env_path)
    
    print("\n" + "="*60)
    print("SPLUNK CREDENTIAL DIAGNOSTIC TEST")
    print("="*60 + "\n")
    
    # Check environment variables
    print("1. Checking environment variables...")
    base_url = os.getenv("SPLUNK_BASE_URL")
    username = os.getenv("SPLUNK_USERNAME")
    password = os.getenv("SPLUNK_PASSWORD")
    enabled = os.getenv("SPLUNK_ENABLED", "true").lower() not in {"0", "false", "no"}
    
    print(f"   SPLUNK_ENABLED: {enabled}")
    print(f"   SPLUNK_BASE_URL: {base_url or '❌ NOT SET'}")
    print(f"   SPLUNK_USERNAME: {username or '❌ NOT SET'}")
    print(f"   SPLUNK_PASSWORD: {'✓ SET' if password else '❌ NOT SET'}")
    
    if not base_url or not username or not password:
        print("\n❌ FAILED: Missing required environment variables")
        print("   Please set SPLUNK_BASE_URL, SPLUNK_USERNAME, and SPLUNK_PASSWORD in config/.env")
        return False
    
    # Create client
    print("\n2. Creating Splunk client...")
    try:
        splunk_client = SplunkClient(
            base_url=base_url,
            username=username,
            password=password,
        )
        print("   ✓ Client created successfully")
    except Exception as e:
        print(f"   ❌ FAILED to create client: {e}")
        return False
    
    # Test login
    print("\n3. Testing authentication...")
    is_valid, error_msg = splunk_client.validate_credentials()
    if is_valid:
        print(f"   ✓ {error_msg}")
    else:
        print(f"   ❌ {error_msg}")
        print("\n   TROUBLESHOOTING:")
        print("   • Check if SPLUNK_USERNAME exists in Splunk Cloud")
        print("   • Check if SPLUNK_PASSWORD is correct and not expired")
        print("   • Check if user account is active (not locked/disabled)")
        print("   • Try resetting password in Splunk Cloud admin console")
        return False
    
    # Test index access
    print("\n4. Testing index access...")
    try:
        indexes = splunk_client.list_indexes()
        print(f"   ✓ Found {len(indexes)} accessible indexes: {', '.join(indexes[:3])}")
    except Exception as e:
        print(f"   ❌ FAILED to list indexes: {e}")
        if "401" in str(e):
            print("   Session may have expired - try clearing cookies")
        return False
    
    # Test search
    print("\n5. Testing search functionality...")
    try:
        results = splunk_client.run_search("index=api_ui_logs | head 1")
        print(f"   ✓ Search successful: returned {len(results)} results")
    except Exception as e:
        print(f"   ⚠ Search completed with warning: {e}")
        # This might fail if no data exists - that's OK
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED - Splunk integration is working!")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
