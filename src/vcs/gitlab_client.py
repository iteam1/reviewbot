"""
GitLab VCS client implementation.
"""
import requests
from typing import Dict, Any
from .base import BaseVCSClient


class GitLabClient(BaseVCSClient):
    """GitLab API client for fetching diffs and posting comments"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gitlab.com/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": api_key,
            "Content-Type": "application/json"
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
        Get diff of a merge request
        Expected kwargs: project_id, merge_request_iid
        """
        project_id = kwargs.get('project_id')
        merge_request_iid = kwargs.get('merge_request_iid')
        
        if not all([project_id, merge_request_iid]):
            raise ValueError("Missing required parameters: project_id, merge_request_iid")
        
        try:
            response = requests.get(
                f"{self.base_url}/projects/{project_id}/merge_requests/{merge_request_iid}/diffs",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Convert GitLab diff objects to unified diff format
            files = response.json()
            diff_parts = []
            
            for file in files:
                if 'diff' in file and file['diff']:
                    # Use old_path and new_path for file headers
                    old_path = file.get('old_path', file.get('new_path', 'unknown'))
                    new_path = file.get('new_path', file.get('old_path', 'unknown'))
                    
                    diff_parts.append(f"--- a/{old_path}")
                    diff_parts.append(f"+++ b/{new_path}")
                    diff_parts.append(file['diff'])
                    diff_parts.append("")  # Empty line between files
            
            return "\n".join(diff_parts)
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch diff: {e}")
    
    def post_comment(self, **kwargs) -> Dict[str, Any]:
        """
        Post comment to a merge request
        Expected kwargs: project_id, merge_request_iid, body
        """
        project_id = kwargs.get('project_id')
        merge_request_iid = kwargs.get('merge_request_iid')
        body = kwargs.get('body')
        
        if not all([project_id, merge_request_iid, body]):
            raise ValueError("Missing required parameters: project_id, merge_request_iid, body")
        
        try:
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/merge_requests/{merge_request_iid}/notes",
                headers=self.headers,
                json={"body": body},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise Exception(f"Failed to post comment: {e}")
