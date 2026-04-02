#!/usr/bin/env python
"""
Test script to demonstrate graceful shutdown of the agent.
This shows how Ctrl+C will now properly stop the agent.
"""

import time
import signal

# Test graceful shutdown
print("=" * 70)
print("Testing Graceful Shutdown - Agent Loop")
print("=" * 70)

shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    print("\n✋ Shutdown signal received - stopping gracefully...")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("\n✅ Agent starting (try pressing Ctrl+C)...\n")

run_count = 0
polling_interval = 300  # 5 minutes

while not shutdown_requested:
    try:
        run_count += 1
        print(f"[Run #{run_count}] Processing incidents...")
        
        # Simulate processing
        time.sleep(2)
        print(f"[Run #{run_count}] ✓ Processing complete")
        
        # Interruptible sleep
        if not shutdown_requested:
            remaining = 10  # Use 10 seconds for demo instead of 300
            print(f"[Run #{run_count}] ⏳ Waiting 10 seconds... (Press Ctrl+C to stop)")
            
            while remaining > 0 and not shutdown_requested:
                sleep_duration = min(1, remaining)
                time.sleep(sleep_duration)
                remaining -= sleep_duration
                
                # Show progress
                if remaining > 0 and not shutdown_requested:
                    print(f"    ...{remaining}s remaining", end='\r')
            
            if not shutdown_requested:
                print(f"    ✓ Resuming next cycle" + " " * 30)
        
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user (Ctrl+C)")
        shutdown_requested = True
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        break

print("\n✅ Agent shutting down gracefully")
print("=" * 70)
