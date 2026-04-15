# AI Service Setup on OpenShift POC

This guide explains how to deploy and use the REAL AI analysis service on OpenShift POC.

## Architecture

```
POC Dashboard → ai-service (port 5001) → MCP Queue (SQLite)
                                             ↓
                                    Claude Code (via port-forward)
                                    analyzes and submits results
```

## Deployment

### 1. Push Latest Code

```bash
cd /Users/rrasouli/Documents/GitHub/ci-failure-tracker/dashboard
git add -A
git commit -m "Add AI service for OpenShift"
git push upstream master
```

### 2. Deploy AI Service

```bash
oc project winc-dashboard-poc

# Deploy the AI service (local_service + MCP server)
oc apply -f openshift/poc/ai-service-deployment.yaml

# Trigger new build to include latest code
oc start-build winc-dashboard-poc

# Wait for build
oc get builds -w

# Update dashboard deployment with AI service URL
oc apply -f openshift/poc/dashboard-deployment.yaml

# Wait for rollout
oc rollout status deployment/winc-dashboard-poc
oc rollout status deployment/ai-service
```

### 3. Verify AI Service

```bash
# Check pods are running
oc get pods -l app=ai-service

# Test health endpoint
oc exec deployment/ai-service -c local-service -- curl -s http://localhost:5001/health
```

Should return:
```json
{
  "status": "ok",
  "mode": "local-claude-code-mcp",
  "message": "Local AI service is running - Connect Claude Code to MCP server for REAL AI!"
}
```

## Usage

### Connect Claude Code to Process Requests

**Step 1: Port Forward MCP Server**

In a terminal, run:
```bash
oc port-forward deployment/ai-service 9999:9999
```

Wait, the MCP server doesn't expose a port - it's stdio-based. Let me revise...

Actually, we need a different approach for OpenShift. Let me create a simple HTTP wrapper around the MCP queue:

### Access the Queue via kubectl/oc exec

The simplest approach is to use `oc exec` to access the queue:

```bash
# Check for pending requests
oc exec deployment/ai-service -c mcp-server -- python3 -c "
import sys
sys.path.insert(0, 'src')
from ai.mcp_server import AnalysisQueue
import json

queue = AnalysisQueue()
requests = queue.get_pending_requests()
print(json.dumps(requests, indent=2))
"
```

## Processing Analysis Requests

### Option 1: Manual Processing (Quick Start)

1. **Check for requests:**
```bash
oc exec deployment/ai-service -c mcp-server -- python3 -c "
import sys; sys.path.insert(0, 'src')
from ai.mcp_server import AnalysisQueue
requests = AnalysisQueue().get_pending_requests()
for r in requests:
    print(f\"Request {r['request_id']}: {r['test_name']} on {r['platform']}\")
"
```

2. **Tell Claude Code to analyze them** (in this session):
```
Analyze the pending requests in the OpenShift AI service queue
```

3. **Submit results:**
```bash
# Claude Code will provide the analysis
# Then run:
oc exec deployment/ai-service -c mcp-server -- python3 -c "
import sys; sys.path.insert(0, 'src')
from ai.mcp_server import AnalysisQueue

queue = AnalysisQueue()
queue.submit_response('REQUEST_ID_HERE', {
    'root_cause': '...',
    'component': '...',
    'confidence': 85,
    # ... rest of analysis
})
"
```

### Option 2: Automated Loop

I'll create a simple script you can run to auto-process:

```bash
# In this Claude Code session, run:
while true; do
  echo "Checking queue..."
  oc exec deployment/ai-service -c mcp-server -- python3 src/ai/process_queue.py
  sleep 30
done
```

## Testing

1. Go to POC dashboard: https://winc-dashboard-poc-winc-dashboard-poc.apps.build10.ci.devcluster.openshift.com
2. Click "AI Analyze" on any failing test
3. Check the queue (see above)
4. Tell Claude Code to analyze it
5. Submit the results
6. Refresh the dashboard - see REAL AI analysis!

## Troubleshooting

**"Local service unavailable"**
- Check ai-service pod is running: `oc get pods -l app=ai-service`
- Check logs: `oc logs deployment/ai-service -c local-service`

**"Analysis timeout"**
- This means the request was queued but not analyzed within 60 seconds
- Check the queue: `oc exec deployment/ai-service -c mcp-server -- python3 -c "..."`
- Analyze the pending requests manually

**Dashboard not using AI service**
- Verify LOCAL_AI_SERVICE_URL is set: `oc get deployment winc-dashboard-poc -o yaml | grep LOCAL_AI`
- Should show: `value: "http://ai-service:5001"`
