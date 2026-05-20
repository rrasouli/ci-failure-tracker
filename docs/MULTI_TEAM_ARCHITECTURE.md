# Multi-Team Dashboard Architecture

## Problem

The CI failure tracker currently serves one team (Windows Containers QE). Other component teams need the same capability. Managers need a single view showing release readiness across all teams.

## Architecture Overview

```
                         +---------------------------+
                         |     Meta-Dashboard        |
                         |  (Release Readiness View) |
                         +---------------------------+
                                    |
                    Polls /api/team-status from each
                    team dashboard every 5 minutes
                                    |
            +----------+----------+---------+----------+
            |          |          |         |          |
       +---------+ +---------+ +---------+ +---------+
       |  WINC   | | Storage | |Networking| |  Your   |
       |Dashboard| |Dashboard| |Dashboard | | Team    |
       +---------+ +---------+ +---------+ +---------+
            |          |          |         |
         SQLite     SQLite     SQLite    SQLite
            |          |          |         |
       Prow/RP    Prow/RP    Prow/RP   Prow/RP
```

Each team deploys their own dashboard instance (separate OpenShift pod). The meta-dashboard is a separate lightweight app that aggregates all teams.

## Components

### 1. Team Dashboard (existing app, per-team instance)

Each team gets their own deployment of the current dashboard. They customize:

- `config.yaml` -- job patterns, versions, platforms, test suite filter
- Data source -- ReportPortal or Prow GCS collector
- Jira project -- team-specific project key and components

What changes:
- New `/api/team-status` endpoint added to the existing Flask app
- New `team:` section in `config.yaml` for team identity (name, ID)
- Two new database query methods for classification counts and Jira counts

The `/api/team-status` endpoint returns a standardized JSON payload:

```json
{
  "team": {
    "name": "Windows Containers QE",
    "id": "winc",
    "dashboard_url": "https://winc-dashboard.apps.cluster.example.com"
  },
  "versions": [
    {
      "version": "4.22",
      "pass_rate": 87.5,
      "total_tests": 142,
      "trend": "improving",
      "platforms": ["aws", "azure", "gcp", "vsphere"]
    }
  ],
  "top_failing_tests": [
    {
      "test_name": "OCP-12345",
      "pass_rate": 12.5,
      "failed_platforms": "aws,gcp",
      "version": "4.22"
    }
  ],
  "classifications": {
    "product_bug": 12,
    "automation_bug": 8,
    "system_issue": 3,
    "transient": 5,
    "unclassified": 42
  },
  "jira": {
    "open_bugs": 23,
    "bugs_with_jira": 20,
    "bugs_without_jira": 65
  },
  "data_freshness": {
    "last_collection": "2026-05-10T09:00:00Z"
  }
}
```

### 2. Meta-Dashboard (new app)

A separate lightweight Flask app with no database. Its only job is to:

1. Read a `registry.yaml` file listing all team dashboard URLs
2. Poll each team's `/api/team-status` endpoint in parallel
3. Render a manager-friendly overview page

Registry format:

```yaml
teams:
  - id: winc
    name: "Windows Containers QE"
    dashboard_url: "https://winc-dashboard.apps.cluster.example.com"
    service_url: "http://winc-dashboard.winc-dashboard.svc.cluster.local:8080"

  - id: storage
    name: "Storage QE"
    dashboard_url: "https://storage-dashboard.apps.cluster.example.com"
    service_url: "http://storage-dashboard.storage-dashboard.svc.cluster.local:8080"

refresh_interval: 300
release_versions:
  - "4.21"
  - "4.22"
```

The `service_url` is used for in-cluster communication (faster, no TLS overhead). Falls back to `dashboard_url` for external access.

### 3. Manager View

The meta-dashboard shows:

- Release readiness score per OCP version (weighted average of all teams' pass rates)
- One card per team with:
  - Team name (links to full dashboard)
  - Pass rate per version
  - Status color: green (>85%), yellow (70-85%), red (<70%)
  - Open Jira bug count
  - Classification breakdown bar
  - Top 3 failing tests
  - Data freshness indicator
- Offline teams section (dashboards that are unreachable)
- Version selector dropdown to filter by OCP version

### 4. Parameterized Deployment

An OpenShift Template parameterized by `TEAM_ID`:

```bash
./team-deploy.sh storage storage-dashboard
```

This creates: namespace, image stream, build config, PVC, config map, deployment, service, route -- all labeled `team: ${TEAM_ID}`.

## Team Onboarding Flow

1. Copy `teams/template.yaml` to `teams/YOUR_TEAM.yaml`
2. Fill in: team name, job patterns, versions, platforms, Jira project, test suite filter
3. Deploy: `./openshift/team-deploy.sh YOUR_TEAM_ID`
4. Update ConfigMap with real config.yaml
5. Register with meta-dashboard: add entry to `registry.yaml` ConfigMap
6. Verify: check `/api/team-status` returns data

## Phases

### Phase 1: Component Teams (this document)
- `/api/team-status` endpoint on each team dashboard
- Meta-dashboard aggregator app
- Parameterized OpenShift deployment
- Self-service onboarding docs

### Phase 2: CI Jobs View (future)
- Job-level stats in `/api/team-status` (total jobs, passed, failed per platform)
- Job health cards in meta-dashboard
- Job trend graphs

## Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Team isolation | Separate pods per team | Teams own their data and config independently |
| Team discovery | File-based registry | Simple, no external dependency. Future: K8s label discovery |
| Meta-dashboard storage | None (stateless) | Pure aggregator, no data to store |
| Communication | In-cluster service URLs | Fast, no TLS overhead, falls back to external URL |
| Authentication | None (POC) | Internal tool, read-only. Future: add SSO if needed |
| Caching | None | Small number of teams (5-10), parallel fetch completes in <2s |

## What This Does NOT Include

- No database schema changes to existing dashboards
- No authentication/authorization layer
- No Kubernetes API-based service discovery (kept simple with file registry)
- No CI job stats (Phase 2)
- No cross-team test deduplication
