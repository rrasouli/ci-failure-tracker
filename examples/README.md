# Example Configurations

This directory contains example configurations for different QE teams.

## Available Examples

- **`networking-team-config.yaml`** - Configuration for Networking QE team
- **`storage-team-config.yaml`** - Configuration for Storage QE team

## How to Use

1. **Choose the example closest to your team** or start with a blank config

2. **Copy to the dashboard directory:**
   ```bash
   cp examples/networking-team-config.yaml dashboard/config.yaml
   ```

3. **Customize for your team:**
   - Update `job_patterns` to match your periodic CI jobs
   - Adjust `versions` (e.g., 4.21, 4.22, 4.23)
   - Set `platforms` your team tests on
   - Update `blocklist` with tests to exclude

4. **Set up authentication:**
   ```bash
   export REPORTPORTAL_API_TOKEN="your-token-here"
   ```

5. **Collect data and run:**
   ```bash
   cd dashboard
   ./dashboard.py collect --days 30
   ./dashboard.py serve
   ```

## Finding Your Job Patterns

To find job patterns for your team:

1. **Check Prow jobs:**
   - Browse: https://prow.ci.openshift.org/
   - Search for your component name

2. **Check ReportPortal:**
   - Visit: https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com
   - Project: `prow`
   - Search for launches containing your component

3. **Common patterns:**
   - `periodic-ci-openshift-{component}-release-{version}-*`
   - `periodic-ci-{org}-{repo}-release-{version}-*`

## Need Help?

- See `../CONTRIBUTING.md` for detailed customization guide
- Open an issue if you need assistance
- Check `../dashboard/README.md` for full documentation

## Contributing Your Example

If you create a configuration for your team and want to share it:

1. Add your example to this directory
2. Update this README with a link
3. Submit a PR

This helps other teams get started faster!
