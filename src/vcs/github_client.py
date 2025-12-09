"""
GitHub VCS client implementation.
"""
import requests
from typing import Dict, Any
from .base import BaseVCSClient


class GitHubClient(BaseVCSClient):
    """GitHub API client for fetching diffs and posting comments"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def verify_connection(self) -> bool:
        """Test if the API key and connection are valid"""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_diff(self, **kwargs) -> str:
        """
        Get diff of a pull request
        Expected kwargs: owner, repo, pull_number
        """
        owner = kwargs.get('owner')
        repo = kwargs.get('repo')
        pull_number = kwargs.get('pull_number')
        
        if not all([owner, repo, pull_number]):
            raise ValueError("Missing required parameters: owner, repo, pull_number")
        
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Convert file objects to unified diff format
            files = response.json()
            diff_parts = []
            
            for file in files:
                if 'patch' in file and file['patch']:
                    diff_parts.append(f"--- a/{file['filename']}")
                    diff_parts.append(f"+++ b/{file['filename']}")
                    diff_parts.append(file['patch'])
                    diff_parts.append("")  # Empty line between files
            
            return "\n".join(diff_parts)
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch diff: {e}")
    
    def post_comment(self, **kwargs) -> Dict[str, Any]:
        """
        Post comment to a pull request
        Expected kwargs: owner, repo, issue_number, body
        """
        owner = kwargs.get('owner')
        repo = kwargs.get('repo')
        issue_number = kwargs.get('issue_number')
        body = kwargs.get('body')
        
        if not all([owner, repo, issue_number, body]):
            raise ValueError("Missing required parameters: owner, repo, issue_number, body")
        
        try:
            response = requests.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                headers=self.headers,
                json={"body": body},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise Exception(f"Failed to post comment: {e}")
