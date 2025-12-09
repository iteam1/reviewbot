import textwrap
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel


class SimpleCodeReviewAgent:
    def __init__(self, llm_client: BaseChatModel, model_name: str):
        """
        Simple code review agent
        Args:
            llm_client: LLM client
            model_name: LLM model name
        """
        self.llm_client = llm_client
        self.model_name = model_name
    
    def say_hello(self) -> str:
        """
        Simple greeting to test the LLM connection
        """
        try:
            messages = [
                HumanMessage(content="Say hello and introduce yourself as a code review agent!")
            ]
            response = self.llm_client.invoke(messages)
            return response.content
        except Exception as e:
            return f" Error: {e}"
    
    def review_code(self, diff: str, external_knowledge: str = "") -> str:
        """
        Review code
        Args:
            diff: Code diff to review
            external_knowledge: Optional external knowledge
        Returns:
            Review comment
        """
        try:
            # System prompt for code review
            system_prompt = textwrap.dedent("""
            You are an expert code reviewer. Analyze the provided code diff and give constructive feedback.
            
            Focus on:
            - Code quality and best practices
            - Potential bugs or issues  
            - Performance considerations
            - Security concerns
            - Readability and maintainability
            
            Provide specific, actionable feedback. Be constructive and helpful.
            Format your response as a clear, professional code review comment.
            """).strip()
            
            # Build user message
            user_content = f"Please review this code diff:\n\n```diff\n{diff}\n```"
            
            if external_knowledge:
                user_content += f"\n\nAdditional context:\n{external_knowledge}"
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ]
            
            # Get review from LLM
            response = self.llm_client.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"❌ Error during code review: {e}"