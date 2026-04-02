#!/usr/bin/env python
"""Test GPT-OSS-120B with timeout"""

import os
import signal
from dotenv import load_dotenv

# Load environment
load_dotenv("config/.env")

api_key = os.getenv("NVIDIA_API_KEY")
print(f"✓ API Key loaded: {api_key[:30]}...")

# Test imports
try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    print("✓ ChatNVIDIA imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

def timeout_handler(signum, frame):
    raise TimeoutError("Request timed out after 30 seconds")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

try:
    print("\n🔧 Initializing ChatNVIDIA...")
    client = ChatNVIDIA(
        model="openai/gpt-oss-120b",
        api_key=api_key,
        temperature=0.1,  # Lower temp for more consistent output
        top_p=0.9,
        max_completion_tokens=512,  # Reduced for faster response
    )
    print("✓ Client initialized")
    
    print("\n📝 Sending test prompt...")
    prompt = "What causes database timeouts?"
    
    full_response = ""
    full_reasoning = ""
    
    for chunk in client.stream([{"role": "user", "content": prompt}]):
        print(".", end="", flush=True)
        if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
            full_reasoning += chunk.additional_kwargs["reasoning_content"]
        if chunk.content:
            full_response += chunk.content
    
    signal.alarm(0)  # Cancel alarm
    print("\n\n✓ Streaming completed!")
    
    print(f"\n📊 Stats:")
    print(f"  Response length: {len(full_response)} chars")
    print(f"  Reasoning length: {len(full_reasoning)} chars")
    
    if full_response:
        print(f"\n💬 Response (first 300 chars):")
        print(f"  {full_response[:300]}...")
    
    if full_reasoning:
        print(f"\n🧠 Reasoning (first 300 chars):")
        print(f"  {full_reasoning[:300]}...")
    else:
        print(f"\n⚠️  No reasoning content in response")
        
except TimeoutError:
    print("\n❌ Request timed out - model may be overloaded or unresponsive")
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    signal.alarm(0)  # Cancel alarm
