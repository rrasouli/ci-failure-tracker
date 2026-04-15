# Vertex AI Setup for AI-Powered Failure Analysis

The dashboard supports AI-powered failure analysis using Anthropic Claude via Google Vertex AI.

## Prerequisites

1. Access to Google Cloud Platform (GCP) with Vertex AI enabled
2. A GCP service account with Vertex AI permissions
3. Anthropic models enabled in your GCP project

## Setup Steps

### 1. File Velocity AI Intake (Recommended)

As mentioned by Josh Boyer, for programmatic access to Vertex AI you should:
- File an intake with the Velocity AI team
- Request a service account with appropriate Vertex AI permissions
- Get the project ID and region for your Vertex AI deployment

### 2. Create OpenShift Secrets

Once you have the credentials, create the following secrets in your OpenShift namespace:

```bash
# Project ID and region
oc create secret generic vertex-ai-credentials \
  --from-literal=project-id=YOUR_PROJECT_ID \
  --from-literal=region=YOUR_REGION

# Service account JSON key
oc create secret generic vertex-ai-service-account \
  --from-file=credentials.json=/path/to/service-account-key.json
```

### 3. Verify Configuration

The deployment will automatically pick up these secrets if they exist. Check the logs:

```bash
oc logs deployment/winc-dashboard-poc | grep -i vertex
```

You should see:
```
Vertex AI client initialized (project: your-project-id, region: your-region)
```

## How It Works

The analyzer uses a 3-tier fallback system:

1. **Local Claude Code (FREE)** - Tries the MCP-based service first (10s timeout)
2. **Vertex AI (~$0.02/analysis)** - Falls back to Vertex AI if configured
3. **Pattern Matching (FREE)** - Falls back to built-in patterns if no AI available

## Environment Variables

The following environment variables control Vertex AI access:

- `ANTHROPIC_VERTEX_PROJECT_ID` - Your GCP project ID
- `ANTHROPIC_VERTEX_REGION` - Vertex AI region (e.g., us-east5)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON (auto-mounted at `/var/secrets/vertex-ai/credentials.json`)

## Testing

To test if Vertex AI is working:

```bash
# Check if client initialized
oc logs deployment/winc-dashboard-poc | grep "Vertex AI client initialized"

# Trigger an analysis
curl -X POST https://winc-dashboard-poc-winc-dashboard-poc.apps.build10.ci.devcluster.openshift.com/api/analyze-failure \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "OCP-71173",
    "platform": "vsphere",
    "version": "4.22",
    "error_message": "test error",
    "use_cached": false
  }'
```

Look for `"analysis_mode": "anthropic-api"` in the response (Vertex AI uses the same mode as direct API).

## Cost Estimation

- Each analysis costs approximately $0.02 (using Claude Sonnet)
- Analyses are cached in the database to avoid duplicate costs
- Most users will see pattern matching (free) due to the 10s timeout
- Vertex AI is only used when pattern matching can't determine the issue

## Troubleshooting

### "Neither Vertex AI credentials nor CLAUDE_API_KEY set"

Both secrets are optional. The system will work with pattern matching alone.

### "Failed to initialize Vertex AI client"

Check:
1. Service account has Vertex AI permissions
2. Anthropic models are enabled in your GCP project
3. Secret `vertex-ai-service-account` contains valid JSON
4. Project ID and region are correct

### Import Error

If you see "anthropic package not installed":
```bash
# Check requirements.txt includes anthropic[vertex]
grep anthropic dashboard/requirements.txt
```

The requirements.txt should include:
```
anthropic[vertex]>=0.18.0
```
