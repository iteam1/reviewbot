"""
GitLab webhook handler for ReviewBot
"""
import logging
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header

from langchain_openai import ChatOpenAI
from src.vcs.gitlab_client import GitLabClient
from src.agent.langchain_agent import LangChainCodeReviewAgent, ReviewContext

logger = logging.getLogger(__name__)

gitlab_webhook_router = APIRouter()

def _verify_token(token: str) -> bool:
    """Verify GitLab webhook token"""
    expected_token = os.getenv("GITLAB_WEBHOOK_TOKEN")
    if not expected_token:
        return True  # No token verification if not configured
    return token == expected_token

@gitlab_webhook_router.post("/")
async def handle_gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(None),
    x_gitlab_token: str = Header(None)
):
    """Handle GitLab webhook events"""
    try:
        payload = await request.json()
        
        logger.info(f"Received GitLab webhook: {x_gitlab_event}")
        
        # Verify token if configured
        if not _verify_token(x_gitlab_token):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Only handle merge request events
        if x_gitlab_event != "Merge Request Hook":
            return {"message": "Event ignored", "event_type": x_gitlab_event}
        
        return await _handle_merge_request(payload)
    
    except Exception as e:
        logger.error(f"Error handling GitLab webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _handle_merge_request(payload: Dict[str, Any]) -> Dict[str, str]:
    """Handle merge request opened/updated events"""
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action")
    if action not in ["open", "update"]:
        return {"message": f"MR action '{action}' ignored"}
    
    project = payload["project"]
    project_id, project_name = project["id"], project["path_with_namespace"]
    mr_iid, author = attrs["iid"], payload["user"]["username"]
    
    logger.info(f"Processing MR !{mr_iid} in {project_name} by {author}")
    
    # Get diff
    gitlab = GitLabClient(api_key=os.getenv("GITLAB_TOKEN"))
    diff = gitlab.get_diff(project_id=project_id, merge_request_iid=mr_iid)
    if not diff:
        return {"message": "No changes to review"}
    
    # Review with LangChain agent
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        base_url=os.getenv("API_BASE_URL"),
        api_key=os.getenv("API_KEY"),
        temperature=0.1
    )
    agent = LangChainCodeReviewAgent(llm)
    context = ReviewContext(repository_name=project_name, pull_request_id=str(mr_iid), author=author)
    response = agent.review_code(diff, context)
    
    # Post comment
    gitlab.post_comment(project_id=project_id, merge_request_iid=mr_iid, body=response.detailed_analysis)
    logger.info(f"Posted review for MR !{mr_iid}")
    return {"message": "Review completed", "mr_iid": mr_iid}
