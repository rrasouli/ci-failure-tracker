#!/usr/bin/env python3
"""
Process analysis queue - displays pending requests

This script is meant to be run inside the OpenShift pod to check for
pending analysis requests. Claude Code can then analyze them and submit results.

Usage (from OpenShift):
    oc exec deployment/ai-service -c mcp-server -- python3 src/ai/process_queue.py

Usage (locally):
    python3 src/ai/process_queue.py
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.mcp_server import AnalysisQueue

queue = AnalysisQueue()
requests = queue.get_pending_requests()

if not requests:
    print("No pending analysis requests.")
    sys.exit(0)

print(f"Found {len(requests)} pending analysis request(s):")
print()

for req in requests:
    print("=" * 70)
    print(f"REQUEST ID: {req['request_id']}")
    print("=" * 70)
    print(f"Test Name: {req['test_name']}")
    print(f"Platform: {req['platform']}")
    print(f"Version: {req['version']}")
    print(f"Created: {req['created_at']}")
    print()
    print("Error Message:")
    print(req['error_message'][:800])
    if len(req['error_message']) > 800:
        print(f"... ({len(req['error_message']) - 800} more chars)")
    print()
    print("Log URL:")
    print(req['log_url'])
    print()

print("=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print()
print("1. Tell Claude Code to analyze these failures")
print("2. For each request, Claude Code will provide analysis")
print("3. Submit results using submit_analysis(request_id, analysis)")
print()
