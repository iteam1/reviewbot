"""
Core models for the reviewbot application.
"""
from .base import BasePullRequest, BaseWebhook, PullRequestState, WebhookAction
from .common import User, Repository
from .github import GitHubWebhook, GitHubPullRequest, GitHubUser, GitHubRepository
from .gitlab import GitLabWebhook, GitLabMergeRequestAttributes, GitLabUser, GitLabProject

__all__ = [
    # Base models
    "BasePullRequest",
    "BaseWebhook", 
    "PullRequestState",
    "WebhookAction",
    
    # Common models
    "User",
    "Repository",
    
    # GitHub models
    "GitHubWebhook",
    "GitHubPullRequest",
    "GitHubUser", 
    "GitHubRepository",
    
    # GitLab models
    "GitLabWebhook",
    "GitLabMergeRequestAttributes",
    "GitLabUser",
    "GitLabProject",
]