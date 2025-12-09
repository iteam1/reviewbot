"""
GitLab-specific webhook models and parsers.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .base import BasePullRequest, BaseWebhook, PullRequestState, WebhookAction


class GitLabUser(BaseModel):
    """GitLab user model"""
    id: int
    name: str
    username: str
    avatar_url: str
    email: str


class GitLabProject(BaseModel):
    """GitLab project model"""
    id: int
    name: str
    description: str
    web_url: str
    git_ssh_url: str
    git_http_url: str
    namespace: str
    path_with_namespace: str
    default_branch: str


class GitLabMergeRequestAttributes(BaseModel):
    """GitLab merge request attributes"""
    id: int
    iid: int  # internal ID
    title: str
    description: str
    state: str  # "opened", "closed", "merged"
    target_branch: str
    source_branch: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    url: str
    action: str  # "open", "close", "merge", etc.


class GitLabWebhook(BaseModel):
    """GitLab webhook payload model"""
    object_kind: str  # "merge_request"
    event_type: str   # "merge_request"
    user: GitLabUser
    project: GitLabProject
    object_attributes: GitLabMergeRequestAttributes

    def to_base_webhook(self) -> BaseWebhook:
        """Convert GitLab webhook to unified BaseWebhook format"""
        # Map GitLab actions to standard actions
        action_mapping = {
            "open": WebhookAction.OPENED,
            "close": WebhookAction.CLOSED,
            "update": WebhookAction.SYNCHRONIZED,
            "merge": WebhookAction.MERGED,
        }
        
        # Map GitLab states to standard states
        state_mapping = {
            "opened": PullRequestState.OPEN,
            "closed": PullRequestState.CLOSED,
            "merged": PullRequestState.MERGED,
        }
        
        base_pr = BasePullRequest(
            id=f"gitlab:{self.object_attributes.id}",
            number=self.object_attributes.iid,
            title=self.object_attributes.title,
            description=self.object_attributes.description,
            author=self.user.username,
            source_branch=self.object_attributes.source_branch,
            target_branch=self.object_attributes.target_branch,
            state=state_mapping.get(self.object_attributes.state, PullRequestState.OPEN),
            created_at=self.object_attributes.created_at,
            updated_at=self.object_attributes.updated_at,
            web_url=self.object_attributes.url,
            repository_name=self.project.path_with_namespace,
            repository_url=self.project.git_http_url,
            platform="gitlab"
        )
        
        return BaseWebhook(
            action=action_mapping.get(self.object_attributes.action, WebhookAction.OPENED),
            pull_request=base_pr
        )