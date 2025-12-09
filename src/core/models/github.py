"""
GitHub-specific webhook models and parsers.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .base import BasePullRequest, BaseWebhook, PullRequestState, WebhookAction


class GitHubUser(BaseModel):
    """GitHub user model"""
    id: int
    login: str
    avatar_url: str
    type: str


class GitHubRepository(BaseModel):
    """GitHub repository model"""
    id: int
    name: str
    full_name: str
    owner: GitHubUser
    private: bool
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str


class GitHubPullRequestHead(BaseModel):
    """GitHub PR head/base branch info"""
    label: str
    ref: str  # branch name
    sha: str
    repo: GitHubRepository


class GitHubPullRequest(BaseModel):
    """GitHub pull request model"""
    id: int
    number: int
    title: str
    body: Optional[str]
    user: GitHubUser
    state: str  # "open", "closed"
    head: GitHubPullRequestHead
    base: GitHubPullRequestHead
    created_at: datetime
    updated_at: datetime
    html_url: str
    merged: Optional[bool] = None


class GitHubWebhook(BaseModel):
    """GitHub webhook payload model"""
    action: str  # "opened", "closed", "synchronize", etc.
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
    sender: GitHubUser

    def to_base_webhook(self) -> BaseWebhook:
        """Convert GitHub webhook to unified BaseWebhook format"""
        # Map GitHub actions to standard actions
        action_mapping = {
            "opened": WebhookAction.OPENED,
            "closed": WebhookAction.CLOSED,
            "synchronize": WebhookAction.SYNCHRONIZED,
        }
        
        # Determine state
        if self.pull_request.merged:
            state = PullRequestState.MERGED
        elif self.pull_request.state == "closed":
            state = PullRequestState.CLOSED
        else:
            state = PullRequestState.OPEN
        
        base_pr = BasePullRequest(
            id=f"github:{self.pull_request.id}",
            number=self.pull_request.number,
            title=self.pull_request.title,
            description=self.pull_request.body,
            author=self.pull_request.user.login,
            source_branch=self.pull_request.head.ref,
            target_branch=self.pull_request.base.ref,
            state=state,
            created_at=self.pull_request.created_at,
            updated_at=self.pull_request.updated_at,
            web_url=self.pull_request.html_url,
            repository_name=self.repository.full_name,
            repository_url=self.repository.clone_url,
            platform="github"
        )
        
        return BaseWebhook(
            action=action_mapping.get(self.action, WebhookAction.OPENED),
            pull_request=base_pr
        )