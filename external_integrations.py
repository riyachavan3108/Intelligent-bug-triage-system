import requests
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitHubIntegration:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.base_url = "https://api.github.com"
    
    async def create_issue(self, bug_report) -> Dict[str, Any]:
        if not self.token or not self.repo:
            logger.warning("GitHub integration not configured")
            return {}
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": bug_report.title,
            "body": f"**Description:**\n{bug_report.description}\n\n"
                   f"**Severity:** {bug_report.severity}\n"
                   f"**Component:** {bug_report.component}\n"
                   f"**Assigned to:** {bug_report.assigned_developer}",
            "assignee": bug_report.assigned_developer.lower().replace(" ", ""),
            "labels": ["bug", bug_report.severity.lower()]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/repos/{self.repo}/issues",
                json=data,
                headers=headers
            )
            return response.json() if response.status_code == 201 else {}
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {str(e)}")
            return {}

class JiraIntegration:
    def __init__(self):
        self.token = os.getenv("JIRA_TOKEN")
        self.url = os.getenv("JIRA_URL")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "BUG")
    
    async def create_ticket(self, bug_report) -> Dict[str, Any]:
        if not self.token or not self.url:
            logger.warning("JIRA integration not configured")
            return {}
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": bug_report.title,
                "description": bug_report.description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": bug_report.severity},
                "assignee": {"displayName": bug_report.assigned_developer}
            }
        }
        
        try:
            response = requests.post(
                f"{self.url}/rest/api/3/issue",
                json=data,
                headers=headers
            )
            return response.json() if response.status_code == 201 else {}
        except Exception as e:
            logger.error(f"Error creating JIRA ticket: {str(e)}")
            return {}