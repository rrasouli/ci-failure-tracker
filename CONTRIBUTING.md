# Contributing to CI Failure Tracker

Thank you for your interest in using or improving this tool!

## For QE Teams: Using This Tool for Your Team

This tool is **generic and designed for any QE team** tracking OpenShift CI periodic jobs.

### Quick Start: Fork and Customize

1. **Fork this repository** to your GitHub account or organization

2. **Choose your tool:**
   - **Dashboard** (recommended): Web-based analytics at `dashboard/`
   - **Jira Bridge**: Automated ticket creation at root level

3. **Customize the configuration:**

   **For Dashboard:**
   - Edit `dashboard/config.yaml`
   - Update `job_patterns` to match your team's periodic CI jobs
   - Adjust `versions` and `platforms` as needed
   - Update `blocklist` with test IDs to exclude

   **For Jira Bridge:**
   - Copy `teams/winc.yaml` to `teams/{your-team}.yaml`
   - Update job patterns, Jira project, and tracking settings

4. **Deploy:**
   - **OpenShift**: See `dashboard/openshift/README.md`
   - **Local**: `cd dashboard && pip install -r requirements.txt && ./dashboard.py serve`

### Example Configurations

**Networking Team:**
```yaml
job_patterns:
  - "periodic-ci-openshift-network-edge-release-{version}-*"
  - "periodic-ci-openshift-ovn-kubernetes-release-{version}-*"
platforms:
  - "aws"
  - "gcp"
  - "azure"
```

**Storage Team:**
```yaml
job_patterns:
  - "periodic-ci-openshift-csi-*-release-{version}-*"
  - "periodic-ci-openshift-storage-*-release-{version}-*"
platforms:
  - "aws"
  - "vsphere"
  - "metal"
```

**Your Team:**
```yaml
job_patterns:
  - "periodic-ci-*-{your-component}-*"
platforms:
  - "aws"  # Adjust to platforms your team tests
```

## Contributing Code

We welcome contributions! Here's how:

### Reporting Issues

- **Bug reports**: Open an issue describing the problem, steps to reproduce, and expected behavior
- **Feature requests**: Open an issue describing the use case and proposed solution
- **Questions**: Open a discussion or issue with the "question" label

### Submitting Changes

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Keep changes focused and atomic
   - Follow existing code style
   - Test your changes locally

3. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: brief description"
   ```

   **Important:** No AI attribution in commits
   - ❌ Don't add: "Co-Authored-By: Claude" or similar
   - ✅ Do add: Clear description of what changed

4. **Push and create a Pull Request:**
   ```bash
   git push origin feature/your-feature-name
   ```

   In your PR:
   - Describe what changed and why
   - Link to related issues
   - Include testing steps if applicable

### Code Style

- **Python**: Follow PEP 8
- **YAML**: Use 2-space indentation
- **Comments**: Explain "why" not "what"
- **No emojis**: Keep code professional

### Testing

- Test dashboard locally before submitting PR
- Verify configuration changes work with sample data
- Check that OpenShift deployment still works

## Project Structure

```
ci-failure-tracker/
├── dashboard/              # Web dashboard (Flask app)
│   ├── src/               # Python source code
│   ├── openshift/         # OpenShift deployment configs
│   ├── config.yaml        # Main configuration (CUSTOMIZE THIS)
│   └── dashboard.py       # CLI entry point
├── teams/                 # Team-specific configs for Jira bridge
│   └── winc.yaml          # Example: Windows Containers team
├── ci_failure_tracker.py  # Jira bridge script
└── README.md

Key files to customize:
- dashboard/config.yaml    # Job patterns, platforms, versions
- teams/{team}.yaml        # Jira bridge team config
```

## Getting Help

- **Documentation**: Check `dashboard/README.md` and `dashboard/USER_GUIDE.md`
- **Issues**: Browse existing issues or create a new one
- **Examples**: See `teams/winc.yaml` for a working configuration

## License

This project is open source. When contributing, you agree that your contributions will be licensed under the same terms as the project.

## Questions?

Open an issue with the "question" label or reach out to the maintainers.

**Remember**: This tool is for **any QE team**. Don't hesitate to fork, customize, and use it for your needs!
