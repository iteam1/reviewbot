"""
FastAPI application for ReviewBot webhook handling
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

from .webhooks.github import github_webhook_router
from .webhooks.gitlab import gitlab_webhook_router

# Configure logging
def setup_logging():
    """Setup logging with console and rotating file handler"""
    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler with rotation (5MB max, keep 3 backups)
    file_handler = RotatingFileHandler(
        log_dir / "reviewbot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    
    # Add file handler to uvicorn and app loggers
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "backend"]:
        log = logging.getLogger(logger_name)
        log.addHandler(file_handler)

setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ReviewBot API",
    description="Code review bot for handling PR webhooks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook routers
app.include_router(github_webhook_router, prefix="/webhooks/github", tags=["GitHub"])
app.include_router(gitlab_webhook_router, prefix="/webhooks/gitlab", tags=["GitLab"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ReviewBot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "reviewbot-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", "8000"))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    
    logger.info(f"Starting ReviewBot API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
