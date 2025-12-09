import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.vcs.github_client import GitHubClient

if __name__ == "__main__":
    # Get token from environment
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("❌ GITHUB_TOKEN not found in environment variables")
        print("Please set GITHUB_TOKEN in your .env file")
        sys.exit(1)
    
    print(f"Using token: {token[:10]}..." if token else "No token")
    
    # Initialize client
    client = GitHubClient(api_key=token)

    print("Testing connection to GitHub...")
    
    # Try to verify connection
    try:
        if client.verify_connection():
            print("✅ Connection to GitHub is successful!")
        else:
            print("❌ Failed to connect to GitHub. Check your token.")
    except Exception as e:
        print(f"❌ Error testing connection: {e}")

    # Try to get diff
    try:
        diff = client.get_diff(
            owner="langchain-ai",
            repo="langchain",
            pull_number=34271
        )
        print(f"✅ Successfully fetched LangChain PR diff!")
        print(f"Diff size: {len(diff)} characters")
        print(f"Preview (first 500 chars):\n{diff[:500]}...")
        
        # Count files changed
        file_count = diff.count("--- a/")
        print(f"Files changed: {file_count}")
        
    except Exception as e:
        print(f"❌ Error fetching LangChain PR: {e}")