"""
GitLab webhook handler for ReviewBot
"""
import logging
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from src.vcs.gitlab_client import GitLabClient
from src.agent.simple_agent import SimpleCodeReviewAgent
from src.agent.advanced_agent import AdvancedCodeReviewAgent
from src.agent.langchain_agent import LangChainCodeReviewAgent

logger = logging.getLogger(__name__)

gitlab_webhook_router = APIRouter()

class GitLabWebhookPayload(BaseModel):
    """GitLab webhook payload model"""
    object_kind: str
    object_attributes: Dict[str, Any]
    project: Dict[str, Any]
    user: Dict[str, Any]

def verify_gitlab_token(token: str) -> bool:
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
        if not verify_gitlab_token(x_gitlab_token):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Handle merge request events
        if x_gitlab_event == "Merge Request Hook":
            return await handle_merge_request_event(payload)
        
        # Handle merge request note events (comments)
        elif x_gitlab_event == "Note Hook":
            return await handle_note_event(payload)
        
        else:
            logger.info(f"Ignoring event type: {x_gitlab_event}")
            return {"message": "Event ignored", "event_type": x_gitlab_event}
    
    except Exception as e:
        logger.error(f"Error handling GitLab webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_merge_request_event(payload: Dict[str, Any]) -> Dict[str, str]:
    """Handle merge request opened/updated events"""
    object_attributes = payload.get("object_attributes", {})
    action = object_attributes.get("action")
    
    # Only process opened and update MRs
    if action not in ["open", "update"]:
        return {"message": f"MR action '{action}' ignored"}
    
    try:
        # Extract MR information
        project_data = payload["project"]
        user_data = payload["user"]
        
        project_id = project_data["id"]
        project_name = project_data["path_with_namespace"]
        mr_iid = object_attributes["iid"]
        mr_author = user_data["username"]
        
        logger.info(f"Processing MR !{mr_iid} in {project_name} by {mr_author}")
        
        # Initialize GitLab client
        gitlab_client = GitLabClient(api_key=os.getenv("GITLAB_TOKEN"))
        
        # Get MR diff
        diff = gitlab_client.get_merge_request_diff(project_id, mr_iid)
        
        if not diff:
            logger.warning(f"No diff found for MR !{mr_iid}")
            return {"message": "No changes to review"}
        
        # Choose review agent based on configuration
        agent_type = os.getenv("REVIEW_AGENT_TYPE", "advanced")
        review_comment = perform_code_review(diff, agent_type, project_name, mr_iid, mr_author)
        
        # Post review comment
        gitlab_client.post_merge_request_comment(project_id, mr_iid, review_comment)
        
        logger.info(f"Posted review comment for MR !{mr_iid}")
        return {"message": "Review completed successfully", "mr_iid": mr_iid}
        
    except Exception as e:
        logger.error(f"Error processing MR event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process MR: {e}")

async def handle_note_event(payload: Dict[str, Any]) -> Dict[str, str]:
    """Handle merge request note events (for follow-up conversations)"""
    object_attributes = payload.get("object_attributes", {})
    noteable_type = object_attributes.get("noteable_type")
    
    # Only process merge request notes
    if noteable_type != "MergeRequest":
        return {"message": "Non-MR note ignored"}
    
    # This can be used for interactive review conversations
    return {"message": "MR note event processed"}

def perform_code_review(diff: str, agent_type: str, project_name: str, mr_iid: int, author: str) -> str:
    """Perform code review using specified agent"""
    try:
        # Initialize LLM client (this should come from config)
        from langchain_openai import ChatOpenAI
        
        llm_client = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            base_url=os.getenv("API_BASE_URL"),
            api_key=os.getenv("API_KEY"),
            temperature=0.1
        )
        
        # Create appropriate agent
        if agent_type == "simple":
            agent = SimpleCodeReviewAgent(llm_client)
            return agent.review_code(diff)
        
        elif agent_type == "advanced":
            agent = AdvancedCodeReviewAgent(llm_client)
            return agent.review_code(diff)
        
        elif agent_type == "langchain":
            from src.agent.langchain_agent import ReviewContext
            agent = LangChainCodeReviewAgent(llm_client)
            context = ReviewContext(
                repository_name=project_name,
                pull_request_id=str(mr_iid),
                author=author
            )
            response = agent.review_code(diff, context)
            return response.detailed_analysis
        
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
    except Exception as e:
        logger.error(f"Error during code review: {e}")
        return f"❌ Error during code review: {e}"
