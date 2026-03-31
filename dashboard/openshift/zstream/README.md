# Z-Stream Dashboard

Dashboard for tracking WINC test results on OCP z-stream releases (4.17, 4.19).

## Configuration

- **Versions tracked:** 4.17, 4.19 (can add 4.18 if needed)
- **Platforms:** AWS, Azure, GCP, Nutanix, vSphere
- **Data source:** ReportPortal
- **Lookback:** 30 days

## Deployment

Deploy to `winc-dashboard` namespace:

```bash
# Apply all resources
oc apply -f dashboard/openshift/zstream/

# Start initial build
oc start-build winc-dashboard-zstream

# Wait for deployment
oc rollout status deployment/winc-dashboard-zstream

# Get dashboard URL
oc get route winc-dashboard-zstream -o jsonpath='{.spec.host}'
```

## Trigger Data Collection

```bash
# Manual collection
curl -X POST https://$(oc get route winc-dashboard-zstream -o jsonpath='{.spec.host}')/api/trigger-collection \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

## Configuration Updates

To update versions or job patterns:

```bash
# Edit ConfigMap
oc edit configmap dashboard-config-zstream

# Restart deployment to reload config
oc rollout restart deployment/winc-dashboard-zstream
```

## Add Version 4.18

If you want to track all three versions (4.17, 4.18, 4.19):

```bash
oc edit configmap dashboard-config-zstream

# Add "4.18" to the versions list under tracking.versions
# Save and restart deployment
oc rollout restart deployment/winc-dashboard-zstream
```
