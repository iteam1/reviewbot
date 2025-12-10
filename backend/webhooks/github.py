"""
GitHub webhook handler for ReviewBot
"""
import logging
import hmac
import hashlib
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks

from langchain_openai import ChatOpenAI
from src.vcs.github_client import GitHubClient
from src.agent.langchain_agent import LangChainCodeReviewAgent, ReviewContext

logger = logging.getLogger(__name__)

github_webhook_router = APIRouter()

def _verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
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
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    """Handle GitHub webhook events"""
    try:
        # Get raw payload
        payload_body = await request.body()
        payload = await request.json()
        
        logger.info(f"Received GitHub webhook: {x_github_event}")
        
        # Verify signature if configured
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if secret and not _verify_signature(payload_body, x_hub_signature_256, secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Only handle pull request events
        if x_github_event != "pull_request":
            return {"message": "Event ignored", "event_type": x_github_event}
        
        # Process in background to avoid webhook timeout
        background_tasks.add_task(_process_pull_request, payload)
        return {"message": "Webhook received, processing in background"}
    
    except Exception as e:
        logger.error(f"Error handling GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _process_pull_request(payload: Dict[str, Any]) -> None:
    """Process pull request in background"""
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        logger.info(f"PR action '{action}' ignored")
        return
    
    pr = payload["pull_request"]
    repo = payload["repository"]
    repo_name, pr_number, author = repo["full_name"], pr["number"], pr["user"]["login"]
    
    logger.info(f"Processing PR #{pr_number} in {repo_name} by {author}")
    
    # Get diff
    github = GitHubClient(api_key=os.getenv("GITHUB_TOKEN"))
    owner, repo = repo_name.split("/")
    diff = github.get_diff(owner=owner, repo=repo, pull_number=pr_number)
    if not diff:
        logger.info("No changes to review")
        return
    
    # Review with LangChain agent
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        base_url=os.getenv("API_BASE_URL"),
        api_key=os.getenv("API_KEY"),
        temperature=0.1
    )
    agent = LangChainCodeReviewAgent(llm)
    context = ReviewContext(repository_name=repo_name, pull_request_id=str(pr_number), author=author)
    response = agent.review_code(diff, context)
    
    # Post comment
    github.post_comment(owner=owner, repo=repo, issue_number=pr_number, body=response.detailed_analysis)
    logger.info(f"Posted review for PR #{pr_number}")
