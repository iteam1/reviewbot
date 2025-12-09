"""
Base models for unified representation across different VCS platforms.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class PullRequestState(str, Enum):
    """Standard pull request states across platforms"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class WebhookAction(str, Enum):
    """Standard webhook actions across platforms"""
    OPENED = "opened"
    CLOSED = "closed"
    SYNCHRONIZED = "synchronized"
    MERGED = "merged"


class BasePullRequest(BaseModel):
    """
    Unified pull request model that all VCS platforms convert to.
    This provides a consistent interface regardless of the source platform.
    """
    id: str  # Platform-specific ID (e.g., "github:123" or "gitlab:456")
    number: int  # PR/MR number
    title: str
    description: Optional[str] = None
    author: str  # Username of the author
    source_branch: str
    target_branch: str
    state: PullRequestState
    created_at: datetime
    updated_at: datetime
    web_url: str  # URL to view the PR/MR
    repository_name: str
    repository_url: str  # Git clone URL
    platform: str  # "github", "gitlab", etc.


class BaseWebhook(BaseModel):
    """
    Base webhook model with common fields.
    Platform-specific webhooks inherit from this.
    """
    action: WebhookAction
    pull_request: BasePullRequest
    
    class Config:
        use_enum_values = True