"""
GitHub webhook handler for ReviewBot
"""
import logging
import hmac
import hashlib
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from src.vcs.github_client import GitHubClient
from src.agent.simple_agent import SimpleCodeReviewAgent
from src.agent.advanced_agent import AdvancedCodeReviewAgent
from src.agent.langchain_agent import LangChainCodeReviewAgent

logger = logging.getLogger(__name__)

github_webhook_router = APIRouter()

class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload model"""
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]

def verify_github_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature:
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

@github_webhook_router.post("/")
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    """Handle GitHub webhook events"""
    try:
        # Get raw payload
        payload_body = await request.body()
        payload = await request.json()
        
        logger.info(f"Received GitHub webhook: {x_github_event}")
        
        # Verify signature if webhook secret is configured
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if webhook_secret and not verify_github_signature(payload_body, x_hub_signature_256, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Handle pull request events
        if x_github_event == "pull_request":
            return await handle_pull_request_event(payload)
        
        # Handle pull request review events
        elif x_github_event == "pull_request_review":
            return await handle_pull_request_review_event(payload)
        
        else:
            logger.info(f"Ignoring event type: {x_github_event}")
            return {"message": "Event ignored", "event_type": x_github_event}
    
    except Exception as e:
        logger.error(f"Error handling GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_pull_request_event(payload: Dict[str, Any]) -> Dict[str, str]:
    """Handle pull request opened/synchronize events"""
    action = payload.get("action")
    
    # Only process opened and synchronize (updated) PRs
    if action not in ["opened", "synchronize"]:
        return {"message": f"PR action '{action}' ignored"}
    
    try:
        # Extract PR information
        pr_data = payload["pull_request"]
        repo_data = payload["repository"]
        
        repo_name = repo_data["full_name"]
        pr_number = pr_data["number"]
        pr_author = pr_data["user"]["login"]
        
        logger.info(f"Processing PR #{pr_number} in {repo_name} by {pr_author}")
        
        # Initialize GitHub client
        github_client = GitHubClient(api_key=os.getenv("GITHUB_TOKEN"))
        
        # Get PR diff
        diff = github_client.get_pull_request_diff(repo_name, pr_number)
        
        if not diff:
            logger.warning(f"No diff found for PR #{pr_number}")
            return {"message": "No changes to review"}
        
        # Choose review agent based on configuration
        agent_type = os.getenv("REVIEW_AGENT_TYPE", "advanced")
        review_comment = perform_code_review(diff, agent_type, repo_name, pr_number, pr_author)
        
        # Post review comment
        github_client.post_pull_request_comment(repo_name, pr_number, review_comment)
        
        logger.info(f"Posted review comment for PR #{pr_number}")
        return {"message": "Review completed successfully", "pr_number": pr_number}
        
    except Exception as e:
        logger.error(f"Error processing PR event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PR: {e}")

async def handle_pull_request_review_event(payload: Dict[str, Any]) -> Dict[str, str]:
    """Handle pull request review events (for follow-up conversations)"""
    # This can be used for interactive review conversations
    return {"message": "PR review event processed"}

def perform_code_review(diff: str, agent_type: str, repo_name: str, pr_number: int, author: str) -> str:
    """Perform code review using specified agent"""
    try:
        # Initialize LLM client (this should come from config)
        from langchain_openai import ChatOpenAI
        import os
        
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
                repository_name=repo_name,
                pull_request_id=str(pr_number),
                author=author
            )
            response = agent.review_code(diff, context)
            return response.detailed_analysis
        
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
    except Exception as e:
        logger.error(f"Error during code review: {e}")
        return f"❌ Error during code review: {e}"
