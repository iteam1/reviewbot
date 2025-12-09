"""
Common models shared across different VCS platforms.
"""
from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """Generic user model that works across platforms"""
    id: int
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None


class Repository(BaseModel):
    """Generic repository model that works across platforms"""
    id: int
    name: str
    full_name: str  # e.g., "owner/repo"
    description: Optional[str] = None
    web_url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    private: bool = False