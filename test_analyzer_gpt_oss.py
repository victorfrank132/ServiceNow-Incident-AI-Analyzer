#!/usr/bin/env python
"""Quick test of the updated incident analyzer with GPT-OSS-120B"""

import sys
sys.path.insert(0, "/Users/apple/Desktop/Snow_TicketAssignment")

from dotenv import load_dotenv
import os

load_dotenv("config/.env")

from src.incident_analyzer import IncidentAnalyzer

api_key = os.getenv("NVIDIA_API_KEY")
print(f"API Key: {api_key[:30]}...")

# Create a test incident
incident = {
    "sys_id": "test123",
    "number": "INC0001234",
    "short_description": "Database connection timeout",
    "description": "Users are experiencing database connection timeouts when trying to save records. This is affecting production systems.",
    "category": "Database",
    "priority": "1"
}

# Create analyzer
team_mappings = {
    "Database": "Database Team",
    "Application": "App Support",
    "Infrastructure": "Infra Team"
}

print("\nInitializing analyzer...")
analyzer = IncidentAnalyzer(None, team_mappings, api_key)
print("✓ Analyzer initialized")

print("\nAnalyzing incident...")
print(f"  Incident: {incident['number']}")
print(f"  Title: {incident['short_description']}")

import time
start = time.time()

try:
    result = analyzer.analyze_incident(incident)
    
    elapsed = time.time() - start
    print(f"\n✓ Analysis complete in {elapsed:.1f}s")
    print(f"  Category: {result.get('category')}")
    print(f"  Confidence: {result.get('confidence')}%")
    print(f"  Root Cause: {result.get('root_cause', '')[:100]}...")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
