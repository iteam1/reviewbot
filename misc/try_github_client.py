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
            owner="locchh",
            repo="spectacle",
            pull_number=1
        )
        print(f"✅ Successfully fetched PR diff!")
        print(f"Diff size: {len(diff)} characters")
        print(f"Preview (first 500 chars):\n{diff[:500]}...")
        
        # Count files changed
        file_count = diff.count("--- a/")
        print(f"Files changed: {file_count}")
        
    except Exception as e:
        print(f"❌ Error fetching PR diff: {e}")

    # Test posting a comment
    print("\nTesting post_comment...")
    try:
        result = client.post_comment(
            owner="locchh",
            repo="spectacle",
            issue_number=1,  # PR #1 (PRs are issues in GitHub API)
            body="🤖 **ReviewBot Test Comment**\n\nThis is a test comment from the reviewbot GitHub client!\n\n✅ Connection and diff fetching working perfectly."
        )
        print(f"✅ Comment posted successfully!")
        print(f"Comment ID: {result.get('id')}")
        print(f"Comment URL: {result.get('html_url')}")
        
    except Exception as e:
        print(f"❌ Error posting comment: {e}")