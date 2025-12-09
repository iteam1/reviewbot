import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import textwrap
from langchain_openai import ChatOpenAI
from src.agent import SimpleCodeReviewAgent


if __name__ == "__main__":
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    print(f"Using OpenAI API key: {api_key[:10]}...")
    
    # Initialize LLM client
    llm_client = ChatOpenAI(
        model="gpt-4",
        api_key=api_key,
        temperature=0.1  # Low temperature for consistent reviews
    )
    
    # Create review agent
    agent = SimpleCodeReviewAgent(
        llm_client=llm_client,
        model_name="gpt-4"
    )
    
    print("Testing SimpleCodeReviewAgent...")
    
    # Test 1: Say hello
    print("\n1. Testing say_hello()...")
    try:
        greeting = agent.say_hello()
        print(f"✅ Agent greeting: {greeting}")
    except Exception as e:
        print(f"❌ Error in say_hello: {e}")
    
    # Test 2: Review code (sample diff)
    print("\n2. Testing review_code()...")
    sample_diff = textwrap.dedent(
        """--- a/example.py
        +++ b/example.py
        @@ -1,3 +1,6 @@
        def calculate_sum(a, b):
        -    return a + b
        +    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        +        raise TypeError("Arguments must be numbers")
        +    return a + b
        
        print(calculate_sum(5, 3))
        """
    )
    
    try:
        review = agent.review_code(
            diff=sample_diff,
            external_knowledge="This is a Python utility function that should handle edge cases properly."
        )
        print(f"✅ Code review:\n{review}")
    except Exception as e:
        print(f"❌ Error in review_code: {e}")