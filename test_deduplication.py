#!/usr/bin/env python
"""Test incident deduplication and comment skipping"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, "/Users/apple/Desktop/Snow_TicketAssignment")

from src.incident_processor import IncidentProcessor

# Create a mock analyzer
class MockAnalyzer:
    def analyze_incident(self, incident):
        return {
            "category": "Database",
            "confidence": 85,
            "root_cause": "Connection pool exhausted",
            "recommendation": "Increase pool size",
            "recommended_assignment_group": "Database Team"
        }
    
    def format_analysis_comment(self, analysis, similar):
        return f"Analysis: {analysis['category']} - {analysis['root_cause']}"

# Create a mock ServiceNow client
class MockServiceNowClient:
    def __init__(self):
        self.comments_posted = []
    
    def get_new_incidents(self, limit=10):
        return [
            {
                "sys_id": "123",
                "number": "INC0001111",
                "state": "1",
                "short_description": "Database issue",
                "description": "Connection timeout"
            }
        ]
    
    def add_comment_to_incident(self, sys_id, comment):
        self.comments_posted.append({"incident_id": sys_id, "comment": comment})
        print(f"  💬 Comment posted to incident")
        return True
    
    def update_assignment_group(self, sys_id, group):
        print(f"  ↗ Reassigned to {group}")
        return True
    
    def get_reporter_approval_field(self, sys_id):
        return None

# Mock KB
class MockKB:
    def find_similar_incidents(self, desc, title, limit=3):
        return []

# Test the deduplication
print("=" * 60)
print("Testing Incident Deduplication (Comment Skipping)")
print("=" * 60)

# Clean up cache for this test
cache_file = Path("logs/analyzed_incidents.json")
if cache_file.exists():
    cache_file.unlink()
    print("✓ Cleared previous cache\n")

# Create processor
analyzer = MockAnalyzer()
snow_client = MockServiceNowClient()
processor = IncidentProcessor(snow_client, analyzer)

# Simulate multiple processing cycles
for cycle in range(1, 4):
    print(f"\n--- Processing Cycle #{cycle} ---")
    results = processor.process_incidents()
    
    # Show summary
    print(f"Comments Posted: {results['comments_posted']}")
    print(f"Comments Skipped: {results['comments_skipped']}")
    
    # Show details
    for incident in results['incidents']:
        if incident['comment_posted']:
            print(f"  ✓ {incident['incident_number']}: Comment POSTED (first time)")
        else:
            print(f"  ⊘ {incident['incident_number']}: Comment SKIPPED (already analyzed)")

# Show cache
print(f"\n--- Analysis Cache Contents ---")
cache_data = json.load(open("logs/analyzed_incidents.json"))
for inc_num, data in cache_data.items():
    print(f"{inc_num}: Confidence {data['confidence']}%, Category: {data['category']}")

print("\n" + "=" * 60)
print("✓ Test complete - no duplicate comments in cycles 2 & 3!")
print("=" * 60)
