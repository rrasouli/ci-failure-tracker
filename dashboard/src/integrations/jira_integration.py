"""
Jira Integration for CI Failure Tracker

Allows creating Jira issues for failing tests with duplicate detection.
"""

import os
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    """Jira configuration"""
    url: str
    project_key: str
    issue_type: str = "Bug"
    component: Optional[str] = None
    priority: str = "Major"


class JiraIntegration:
    """
    Jira integration for filing bugs for failing tests.

    Features:
    - Check for existing Jira before creating new one
    - Link test failure to existing Jira if found
    - Create new Jira with test details if none exists
    """

    def __init__(self, config: JiraConfig):
        self.config = config
        self.enabled = self._check_credentials()

    def _check_credentials(self) -> bool:
        """Check if Jira credentials are available"""
        # Check for Jira API token
        jira_token = os.environ.get('JIRA_API_TOKEN')

        if not jira_token:
            logger.warning("Jira integration disabled: Missing JIRA_API_TOKEN environment variable")
            return False

        return True

    def search_existing_issue(self, test_name: str, version: str, platform: str) -> Optional[Dict]:
        """
        Search for existing Jira issue for this test failure.

        Args:
            test_name: Test ID (e.g., OCP-12345)
            version: OCP version (e.g., 4.22)
            platform: Platform (e.g., aws)

        Returns:
            Jira issue dict if found, None otherwise
        """
        if not self.enabled:
            return None

        # Use Atlassian MCP to search for existing issues
        # JQL query to find issues with this test name
        jql = f'project = {self.config.project_key} AND summary ~ "{test_name}" AND resolution = Unresolved'

        try:
            # This would use the Atlassian MCP server
            # For now, return None to indicate no existing issue
            # In production, this would call: mcp.atlassian.search_issues(jql)
            logger.info(f"Searching for existing Jira: {jql}")
            return None
        except Exception as e:
            logger.error(f"Error searching Jira: {e}")
            return None

    def create_issue(
        self,
        test_name: str,
        test_description: str,
        version: str,
        platform: str,
        error_message: str,
        job_url: str,
        failure_rate: float,
        runs: int,
        failures: int
    ) -> Optional[str]:
        """
        Create a new Jira issue for test failure.

        Args:
            test_name: Test ID (e.g., OCP-12345)
            test_description: Human-readable test description
            version: OCP version
            platform: Platform
            error_message: Error message from test failure
            job_url: Link to job
            failure_rate: Failure rate percentage
            runs: Total runs
            failures: Number of failures

        Returns:
            Jira issue key if created, None otherwise
        """
        if not self.enabled:
            logger.warning("Cannot create Jira: Integration not enabled")
            return None

        # Check for existing issue first
        existing = self.search_existing_issue(test_name, version, platform)
        if existing:
            logger.info(f"Existing Jira found: {existing.get('key')}")
            return existing.get('key')

        # Create issue summary and description
        summary = f"{test_name}: Test failure on {platform} {version}"

        description = f"""
h2. Test Failure Report

*Test:* {test_name}
*Description:* {test_description}
*Version:* {version}
*Platform:* {platform}

h3. Failure Statistics
* Failure Rate: {failure_rate:.1f}%
* Total Runs: {runs}
* Failures: {failures}

h3. Error Message
{{code}}
{error_message[:500]}...
{{code}}

h3. Links
* [Job URL|{job_url}]
* [Dashboard|{os.environ.get('DASHBOARD_URL', 'http://dashboard')}]

---
_This issue was automatically created by CI Failure Tracker_
"""

        try:
            # This would use the Atlassian MCP server to create issue
            # In production: mcp.atlassian.create_issue(...)
            logger.info(f"Would create Jira: {summary}")
            logger.debug(f"Description: {description}")

            # For now, return a mock issue key
            # In production, this would return the actual created issue key
            return None
        except Exception as e:
            logger.error(f"Error creating Jira: {e}")
            return None

    def get_issue_url(self, issue_key: str) -> str:
        """Get URL for a Jira issue"""
        return f"{self.config.url}/browse/{issue_key}"


# Global Jira integration instance
_jira_instance: Optional[JiraIntegration] = None


def get_jira_integration() -> Optional[JiraIntegration]:
    """Get or create Jira integration instance"""
    global _jira_instance

    if _jira_instance is None:
        # Load configuration from environment
        jira_url = os.environ.get('JIRA_URL', 'https://issues.redhat.com')
        jira_project = os.environ.get('JIRA_PROJECT', 'WINC')
        jira_component = os.environ.get('JIRA_COMPONENT')

        config = JiraConfig(
            url=jira_url,
            project_key=jira_project,
            component=jira_component
        )

        _jira_instance = JiraIntegration(config)

    return _jira_instance if _jira_instance.enabled else None
