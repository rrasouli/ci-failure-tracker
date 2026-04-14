"""
Hybrid AI analyzer that tries local Claude Code first, then falls back to API
"""

import os
import requests
import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HybridFailureAnalyzer:
    """
    Hybrid AI analyzer:
    1. Try local Claude Code service first (FREE)
    2. Fall back to Anthropic API if local not available
    """

    def __init__(self):
        self.local_service_url = os.getenv('LOCAL_AI_SERVICE_URL', 'http://localhost:5001')
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')

        # Initialize Anthropic client (for fallback)
        if self.claude_api_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
                logger.info("Anthropic API client initialized (fallback available)")
            except ImportError:
                self.claude_client = None
                logger.warning("anthropic package not installed - API fallback unavailable")
        else:
            self.claude_client = None
            logger.warning("CLAUDE_API_KEY not set - API fallback unavailable")

    def _check_local_service(self) -> bool:
        """Check if local Claude Code service is running"""
        try:
            response = requests.get(
                f"{self.local_service_url}/health",
                timeout=2  # Quick timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Local service check failed: {e}")
            return False

    def analyze_failure(
        self,
        test_name: str,
        error_message: str,
        log_url: str,
        platform: str,
        version: str
    ) -> Dict[str, Any]:
        """
        Analyze failure using hybrid approach:
        1. Try local Claude Code service (FREE)
        2. Fall back to Anthropic API if local not available

        Args:
            test_name: Test identifier (e.g., OCP-39030)
            error_message: Error message from test failure
            log_url: URL to build logs
            platform: Platform (aws, azure, gcp, etc.)
            version: OpenShift version

        Returns:
            Analysis dictionary with root_cause, component, confidence, etc.
        """

        # Try local service first
        logger.info(f"Attempting local Claude Code analysis for {test_name}")
        local_result = self._try_local_analysis(
            test_name, error_message, log_url, platform, version
        )

        if local_result:
            logger.info(f"✓ Used local Claude Code (FREE) for {test_name}")
            local_result['cost'] = 0.0
            local_result['analysis_mode'] = 'local-claude-code'
            return local_result

        # Fall back to API
        logger.info(f"Local service unavailable, falling back to API for {test_name}")
        api_result = self._try_api_analysis(
            test_name, error_message, log_url, platform, version
        )

        if api_result:
            logger.info(f"✓ Used Anthropic API (cost: ~$0.024) for {test_name}")
            api_result['cost'] = 0.024  # Approximate cost with Sonnet
            api_result['analysis_mode'] = 'anthropic-api'
            return api_result

        # Both failed
        logger.error(f"✗ Both local and API analysis failed for {test_name}")
        return {
            'error': 'Analysis unavailable',
            'root_cause': 'Could not analyze - both local service and API unavailable',
            'component': 'unknown',
            'confidence': 0,
            'analysis_mode': 'failed',
            'cost': 0.0
        }

    def _try_local_analysis(
        self,
        test_name: str,
        error_message: str,
        log_url: str,
        platform: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """Try to use local Claude Code service"""
        try:
            # Check if service is running
            if not self._check_local_service():
                logger.debug("Local service not running")
                return None

            # Call local service
            response = requests.post(
                f"{self.local_service_url}/analyze",
                json={
                    'test_name': test_name,
                    'error_message': error_message,
                    'log_url': log_url,
                    'platform': platform,
                    'version': version
                },
                timeout=60  # Allow time for analysis
            )

            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Local analysis succeeded: {result.get('root_cause', '')[:100]}")
                return result
            else:
                logger.warning(f"Local service returned {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            logger.warning("Local service timeout")
            return None
        except Exception as e:
            logger.debug(f"Local service error: {e}")
            return None

    def _try_api_analysis(
        self,
        test_name: str,
        error_message: str,
        log_url: str,
        platform: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """Fall back to Anthropic API"""
        try:
            if not self.claude_client:
                logger.error("No Claude API client available")
                return None

            # Fetch logs (truncated for cost optimization)
            logs = self._fetch_logs(log_url)
            logs_excerpt = logs[-3000:] if len(logs) > 3000 else logs

            # Build prompt
            prompt = f"""Analyze this Windows Containers test failure in OpenShift CI.

**Test:** {test_name}
**Platform:** {platform}
**Version:** {version}
**Error:** {error_message}

**Build Logs (last 3000 chars):**
```
{logs_excerpt}
```

Provide analysis as JSON with these exact fields:
{{
  "root_cause": "1-2 sentence description of what caused the failure",
  "component": "affected component name (e.g., windows-machine-config-operator, kubelet, csi-driver)",
  "confidence": 85,
  "failure_type": "product_bug",
  "platform_specific": true,
  "affected_platforms": ["azure"],
  "evidence": "Key log lines that show the problem",
  "suggested_action": "What should be done next",
  "issue_title": "Bug: [brief description]",
  "issue_description": "Detailed description for Jira/GitHub issue"
}}

Only return the JSON, no additional text.
"""

            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-sonnet-4",  # Cheaper, still capable
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
                logger.debug(f"API analysis succeeded: {analysis.get('root_cause', '')[:100]}")
                return analysis

            # Try parsing entire response as JSON
            try:
                analysis = json.loads(response_text)
                logger.debug(f"API analysis (direct JSON): {analysis.get('root_cause', '')[:100]}")
                return analysis
            except json.JSONDecodeError:
                # Fallback: return raw text
                logger.warning("Could not parse API response as JSON, returning raw text")
                return {
                    'root_cause': response_text[:200],
                    'raw_analysis': response_text,
                    'component': 'unknown',
                    'confidence': 50,
                    'failure_type': 'unknown',
                    'platform_specific': False,
                    'affected_platforms': [platform],
                    'evidence': 'See raw_analysis',
                    'suggested_action': 'Manual investigation needed'
                }

        except Exception as e:
            logger.error(f"API analysis error: {e}")
            return None

    def _fetch_logs(self, log_url: str) -> str:
        """Fetch build logs from URL"""
        try:
            response = requests.get(log_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch logs from {log_url}: {e}")
        return ""
