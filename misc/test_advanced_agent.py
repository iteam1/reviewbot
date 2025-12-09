import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import textwrap
from langchain_openai import ChatOpenAI
from src.agent import AdvancedCodeReviewAgent


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
        temperature=0.1
    )
    
    # Create advanced review agent
    agent = AdvancedCodeReviewAgent(
        llm_client=llm_client,
        model_name="gpt-4"
    )
    
    print("Testing AdvancedCodeReviewAgent...")
    
    # Test with same sample diff as simple agent
    print("\n🔬 Testing advanced review_code()...")
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
    ).strip()
    
    try:
        # Test formatted review
        review = agent.review_code(
            diff=sample_diff,
            external_knowledge="This is a Python utility function that should handle edge cases properly."
        )
        print(f"✅ Advanced Code Review:\n{review}")
        
        print("\n" + "="*80)
        
        # Test structured data
        print("\n📊 Testing structured output...")
        structured = agent.get_structured_review(
            diff=sample_diff,
            external_knowledge="This is a Python utility function that should handle edge cases properly."
        )
        
        print(f"✅ Structured Review Data:")
        print(f"   - Overall Assessment: {structured.overall_assessment}")
        print(f"   - Issues Found: {len(structured.issues)}")
        print(f"   - Positive Aspects: {len(structured.positive_aspects)}")
        print(f"   - Recommendations: {len(structured.recommendations)}")
        print(f"   - Approval Status: {structured.approval_status}")
        
        if structured.issues:
            print(f"\n   📝 Issue Details:")
            for i, issue in enumerate(structured.issues, 1):
                print(f"      {i}. {issue.type} ({issue.severity}): {issue.description}")
        
    except Exception as e:
        print(f"❌ Error in advanced agent: {e}")
        import traceback
        traceback.print_exc()
