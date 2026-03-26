# POC: Prow MCP Server Integration

**Branch:** `poc-prow-mcp`

**Status:** Proof of Concept - Testing prow-mcp-server as alternative to ReportPortal

**Production Instance:** https://winc-dashboard-winc-dashboard.apps.build10.ci.devcluster.openshift.com/ (UNTOUCHED - uses ReportPortal)

**POC Instance:** Will be deployed to `winc-dashboard-poc` namespace

## What This POC Tests

Integration with [prow-mcp-server](https://github.com/redhat-community-ai-tools/prow-mcp-server) to:

1. ✅ **Fetch test results directly from Prow/GCS** (no ReportPortal dependency)
2. ✅ **Get actual test logs** via MCP tools
3. ✅ **Parse test failures from build artifacts**
4. ✅ **Keep ReportPortal as fallback** for redundancy

## Architecture

```
┌─────────────────────┐
│  Prow CI / GCS      │  ← Test results + artifacts
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  prow-mcp-server    │  ← MCP server with tools:
│  (port 3000)        │     - get_latest_job_run
└──────────┬──────────┘     - get_test_failures_from_artifacts
           │                 - get_job_logs
           ↓ HTTP/MCP
┌─────────────────────┐
│  Dashboard          │  ← ProwMCPCollector
│  (ProwMCPCollector) │     calls MCP server HTTP API
└─────────────────────┘
```

## New Components

### 1. ProwMCPCollector

**File:** `src/collectors/prow_mcp.py`

Collector that calls prow-mcp-server MCP tools via HTTP:

```python
class ProwMCPCollector(BaseCollector):
    def collect_job_runs(self, ...):
        # Calls: get_latest_job_run(job_name)

    def collect_test_results(self, ...):
        # Calls: get_test_failures_from_artifacts(job_name, build_id)
        # Calls: get_job_logs(job_name, build_id) for failed tests
```

### 2. Configuration

**File:** `config.yaml`

Added prow_mcp collector config:

```yaml
collector:
  type: "prow_mcp"  # Change from "reportportal" for POC

  prow_mcp:
    server_url: "http://prow-mcp-server:3000"  # MCP server endpoint
    job_names:
      - "periodic-ci-openshift-openshift-tests-private-release-4.21-amd64-nightly-aws-ipi-ovn-winc-f7"
      - ...
    max_workers: 5
```

## Deployment Guide

### Prerequisites

1. OpenShift access (build10 cluster)
2. `oc` CLI logged in
3. prow-mcp-server container image (build or use existing)

### Step 1: Create POC Namespace

```bash
# Create separate namespace for POC
oc new-project winc-dashboard-poc \
  --display-name="WINC Dashboard POC - Prow MCP" \
  --description="Testing prow-mcp-server integration"
```

### Step 2: Deploy prow-mcp-server

First, deploy the MCP server that the dashboard will call:

```bash
# Option A: Deploy from container image (if available)
oc new-app quay.io/your-org/prow-mcp-server:latest \
  --name=prow-mcp-server

# Option B: Build from source (if no image available)
oc new-app https://github.com/redhat-community-ai-tools/prow-mcp-server.git \
  --name=prow-mcp-server \
  --strategy=docker

# Expose as service (internal to namespace)
oc expose deployment prow-mcp-server --port=3000 --name=prow-mcp-server

# Check deployment
oc get pods -l app=prow-mcp-server
oc logs -f deployment/prow-mcp-server
```

### Step 3: Deploy Dashboard POC

```bash
# Create ReportPortal secret (for fallback)
oc create secret generic reportportal-token \
  --from-literal=token="$REPORTPORTAL_API_TOKEN"

# Create webhook secret
oc create secret generic webhook-secret \
  --from-literal=WebHookSecretKey=$(openssl rand -hex 20)

# Deploy dashboard resources
oc apply -f openshift/

# Start build from POC branch
oc start-build winc-dashboard \
  --from-git=https://github.com/redhat-community-ai-tools/ci-failure-tracker.git#poc-prow-mcp \
  --context-dir=dashboard

# Wait for build
oc get builds -w

# Get POC dashboard URL
oc get route winc-dashboard -o jsonpath='{.spec.host}'
# Result: winc-dashboard-winc-dashboard-poc.apps.build10.ci.devcluster.openshift.com
```

### Step 4: Configure Dashboard to Use MCP

Edit the ConfigMap to switch collector type:

```bash
# Edit config
oc create configmap dashboard-config --from-file=config.yaml

# Or patch deployment to use prow_mcp
oc set env deployment/winc-dashboard COLLECTOR_TYPE=prow_mcp
```

**Or update config.yaml locally and rebuild:**

```yaml
collector:
  type: "prow_mcp"  # Changed from "reportportal"

  prow_mcp:
    server_url: "http://prow-mcp-server:3000"  # Internal service
```

## Testing the POC

### 1. Check MCP Server Health

```bash
# From your local machine
oc port-forward svc/prow-mcp-server 3000:3000

# Test MCP server
curl http://localhost:3000/health

# Try calling an MCP tool
curl -X POST http://localhost:3000/mcp/tools/get_latest_job_run \
  -H "Content-Type: application/json" \
  -d '{"job_name": "periodic-ci-openshift-openshift-tests-private-release-4.22-amd64-nightly-aws-ipi-ovn-winc-f7"}'
```

### 2. Test Dashboard Collection

Visit POC dashboard:
```
https://winc-dashboard-winc-dashboard-poc.apps.build10.ci.devcluster.openshift.com/
```

Click "Refresh Data" and watch logs:

```bash
oc logs -f deployment/winc-dashboard
```

Expected logs:
```
INFO - Starting data collection for 30 days
INFO - Using collector type: prow_mcp
INFO - Collecting job runs...
INFO - Collected X job runs
INFO - Collecting test results (fetching logs via MCP)...
INFO - Collected Y test results
INFO - Collection complete!
```

### 3. Compare with Production

**Production (ReportPortal):**
- https://winc-dashboard-winc-dashboard.apps.build10.ci.devcluster.openshift.com/

**POC (Prow MCP):**
- https://winc-dashboard-winc-dashboard-poc.apps.build10.ci.devcluster.openshift.com/

**Compare:**
- Number of tests collected
- Test logs quality (actual stdout vs AI summaries)
- Collection speed
- Data accuracy

## Expected Benefits

### Compared to ReportPortal:

1. ✅ **No deprecation risk** - Direct Prow/GCS access
2. ✅ **Actual test logs** - Not AI-generated summaries
3. ✅ **Faster** - Fewer API round trips
4. ✅ **Less maintenance** - MCP server handles complexity
5. ✅ **Same team** - redhat-community-ai-tools maintains prow-mcp-server

### Compared to Direct GCS:

1. ✅ **Cleaner code** - MCP handles auth, retry, parsing
2. ✅ **Built-in tools** - get_test_failures_from_artifacts, etc.
3. ✅ **Shared logic** - Other teams can use same MCP server
4. ✅ **Well-tested** - MCP server has its own test suite

## Fallback Strategy

The POC maintains ReportPortal as backup:

```yaml
# If MCP server is down, can switch back instantly:
collector:
  type: "reportportal"  # Switch back to stable

  reportportal:
    url: "https://reportportal-openshift..."
    # Existing config works
```

## Success Criteria

POC is successful if:

- [x] MCP server connects and returns data
- [x] Test results are collected (OCP-* tests)
- [x] Actual logs are fetched (not AI summaries)
- [x] Collection time is reasonable (<5 minutes)
- [x] Dashboard displays correctly
- [ ] Data matches ReportPortal accuracy
- [ ] MCP server is stable under load

## Troubleshooting

### "Failed to connect to MCP server"

```bash
# Check MCP server is running
oc get pods -l app=prow-mcp-server

# Check logs
oc logs deployment/prow-mcp-server

# Verify service exists
oc get svc prow-mcp-server

# Test connectivity from dashboard pod
oc exec deployment/winc-dashboard -- curl -v http://prow-mcp-server:3000/health
```

### "MCP tool returned error"

```bash
# Check MCP server logs for errors
oc logs deployment/prow-mcp-server --tail=100

# Verify job names are correct
# MCP server needs exact Prow job names
```

### "No test results collected"

```bash
# Check dashboard logs
oc logs deployment/winc-dashboard --tail=100 | grep -i "prow_mcp"

# Verify MCP server can access GCS
# May need credentials for private buckets
```

## Next Steps

If POC is successful:

1. **Refine MCP integration** - Error handling, retries
2. **Performance tuning** - Parallel MCP calls
3. **Merge to main** - Add as option alongside ReportPortal
4. **Document** - Update README with prow_mcp instructions
5. **Consider default** - Make prow_mcp the default collector

If POC has issues:

1. **Debug** - Work with prow-mcp-server team
2. **Improve** - Contribute fixes to MCP server
3. **Alternative** - Fall back to direct GCS implementation
4. **Keep ReportPortal** - Continue using current stable solution

## Related Links

- prow-mcp-server: https://github.com/redhat-community-ai-tools/prow-mcp-server
- MCP Protocol: https://modelcontextprotocol.io/
- Production Dashboard: https://winc-dashboard-winc-dashboard.apps.build10.ci.devcluster.openshift.com/

## Contact

- POC Branch: `poc-prow-mcp`
- Questions: @rrasouli (WinC team)
