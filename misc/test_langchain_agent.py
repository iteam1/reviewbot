import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import textwrap
from langchain_openai import ChatOpenAI
from src.agent import LangChainCodeReviewAgent, ReviewContext


if __name__ == "__main__":
    # Initialize LLM client
    llm_client = ChatOpenAI(
        model=os.getenv("MODEL_NAME"),
        base_url=os.getenv("API_BASE_URL"),
        api_key=os.getenv("API_KEY"),
        temperature=0.1
    )
    
    # Create LangChain agent
    agent = LangChainCodeReviewAgent(
        llm_client=llm_client,
    )
    
    print("Testing LangChain Code Review Agent...")
    print(f"Available tools: {agent.get_available_tools()}")
    
    # Test with sample diff
    print("\n🤖 Testing LangChain agent with tools...")
    sample_diff = textwrap.dedent(
        """--- a/user_auth.py
        +++ b/user_auth.py
        @@ -1,8 +1,15 @@
         import hashlib
        +import os
         
         def authenticate_user(username, password):
        -    # TODO: Add proper authentication
        -    return username == "admin" and password == "password"
        +    # Hash the password
        +    hashed_password = hashlib.md5(password.encode()).hexdigest()
        +    
        +    # Check against database (simplified)
        +    if username == "admin" and hashed_password == "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8":
        +        return True
        +    return False
         
         def get_user_data(user_id):
        -    return f"SELECT * FROM users WHERE id = {user_id}"
        +    query = f"SELECT * FROM users WHERE id = {user_id}"
        +    return execute_query(query)
        """
    ).strip()
    
    # Create review context
    context = ReviewContext(
        repository_name="security-app",
        pull_request_id="42",
        author="developer123",
        external_knowledge="This is a security-critical authentication module for a web application. Security is paramount."
    )
    
    try:
        print("\n" + "="*80)
        print("🔍 LANGCHAIN AGENT EXECUTION (with tools)")
        print("="*80)
        
        # Execute agent review with thread_id
        review_result = agent.review_code(
            diff=sample_diff,
            context=context,
            thread_id="security-review-1"
        )
        
        print("\n" + "="*80)
        print("📊 STRUCTURED REVIEW RESULTS")
        print("="*80)
        
        print(f"\n✅ Review Summary:")
        print(f"   {review_result.summary}")
        
        print(f"\n📋 Issues Found ({len(review_result.issues_found)}):")
        for i, issue in enumerate(review_result.issues_found, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n💡 Recommendations ({len(review_result.recommendations)}):")
        for i, rec in enumerate(review_result.recommendations, 1):
            print(f"   {i}. {rec}")
        
        print(f"\n🎯 Final Assessment:")
        print(f"   - Approval Status: {review_result.approval_status}")
        print(f"   - Confidence Score: {review_result.confidence_score:.2f}")
        
        print(f"\n📝 Detailed Analysis:")
        print(f"   {review_result.detailed_analysis[:500]}...")
        
        print("\n" + "="*80)
        print("🎉 LANGCHAIN AGENT TEST COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error in LangChain agent: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with a simpler diff for comparison
    print("\n\n🔄 Testing with simpler diff...")
    simple_diff = textwrap.dedent(
        """--- a/math_utils.py
        +++ b/math_utils.py
        @@ -1,3 +1,6 @@
         def add_numbers(a, b):
        -    return a + b
        +    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        +        raise TypeError("Arguments must be numbers")
        +    return a + b
         
         print(add_numbers(5, 3))
        """
    ).strip()
    
    simple_context = ReviewContext(
        repository_name="math-library",
        pull_request_id="1",
        author="mathdev",
        external_knowledge="Simple math utility library with basic functions."
    )
    
    try:
        simple_review = agent.review_code(
            diff=simple_diff,
            context=simple_context,
            thread_id="simple-review-1"
        )
        
        print(f"\n📊 Simple Diff Results:")
        print(f"   - Issues: {len(simple_review.issues_found)}")
        print(f"   - Status: {simple_review.approval_status}")
        print(f"   - Confidence: {simple_review.confidence_score:.2f}")
        
    except Exception as e:
        print(f"❌ Error with simple diff: {e}")
