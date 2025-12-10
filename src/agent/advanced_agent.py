"""
Advanced Code Review Agent using LangChain structured output and multi-step reasoning.
"""
import textwrap
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser


class CodeIssue(BaseModel):
    """Represents a single code issue found during review"""
    type: str = Field(description="Type of issue: bug, performance, security, style, etc.")
    severity: str = Field(description="Severity level: critical, high, medium, low")
    line_range: Optional[str] = Field(description="Line range where issue occurs (e.g., '10-15')")
    description: str = Field(description="Clear description of the issue")
    suggestion: str = Field(description="Specific suggestion to fix the issue")


class ReviewSummary(BaseModel):
    """Structured output for code review"""
    overall_assessment: str = Field(description="Overall assessment of the code changes")
    issues: List[CodeIssue] = Field(description="List of issues found in the code")
    positive_aspects: List[str] = Field(description="Good aspects of the code changes")
    recommendations: List[str] = Field(description="General recommendations for improvement")
    approval_status: str = Field(description="Approval status: approved, needs_changes, rejected")


class AdvancedCodeReviewAgent:
    """Advanced code review agent with structured output and multi-step analysis"""
    
    def __init__(self, llm_client: BaseChatModel, model_name: str):
        """
        Initialize advanced code review agent
        Args:
            llm_client: LangChain LLM client
            model_name: Name of the model being used
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.parser = PydanticOutputParser(pydantic_object=ReviewSummary)
    
    def _analyze_code_changes(self, diff: str) -> str:
        """
        Step 1: Analyze what changes were made
        """
        system_prompt = textwrap.dedent("""
        You are a code analysis expert. Analyze the provided diff and describe:
        1. What files were changed
        2. What type of changes were made (additions, deletions, modifications)
        3. The purpose/intent of these changes
        4. The scope and complexity of the changes
        
        Be concise but thorough.
        """).strip()
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this code diff:\n\n```diff\n{diff}\n```")
        ]
        
        response = self.llm_client.invoke(messages)
        return response.content
    
    def _detect_issues(self, diff: str, analysis: str, external_knowledge: str = "") -> str:
        """
        Step 2: Detect potential issues in the code
        """
        system_prompt = textwrap.dedent("""
        You are a code quality expert. Based on the code diff and analysis, identify potential issues:
        
        Look for:
        - Bugs and logic errors
        - Security vulnerabilities
        - Performance problems
        - Code style violations
        - Design pattern issues
        - Missing error handling
        - Potential edge cases
        
        Be specific about line numbers and provide actionable feedback.
        """).strip()
        
        user_content = f"""
        Code diff:
        ```diff
        {diff}
        ```
        
        Analysis:
        {analysis}
        """
        
        if external_knowledge:
            user_content += f"\n\nProject context:\n{external_knowledge}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        
        response = self.llm_client.invoke(messages)
        return response.content
    
    def _generate_structured_review(self, diff: str, analysis: str, issues: str, external_knowledge: str = "") -> ReviewSummary:
        """
        Step 3: Generate structured review output
        """
        system_prompt = textwrap.dedent(f"""
        You are an expert code reviewer. Generate a comprehensive, structured code review.
        
        {self.parser.get_format_instructions()}
        
        Provide constructive, actionable feedback that helps improve code quality.
        """).strip()
        
        user_content = f"""
        Code diff:
        ```diff
        {diff}
        ```
        
        Code analysis:
        {analysis}
        
        Issues detected:
        {issues}
        """
        
        if external_knowledge:
            user_content += f"\n\nProject context:\n{external_knowledge}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        
        response = self.llm_client.invoke(messages)
        return self.parser.parse(response.content)
    
    def _format_review_comment(self, review: ReviewSummary) -> str:
        """
        Step 4: Format the structured review into a readable comment
        """
        comment_parts = []
        
        # Header with overall assessment
        comment_parts.append(f"## 🤖 Code Review\n\n**Overall Assessment:** {review.overall_assessment}\n")
        
        # Issues section
        if review.issues:
            comment_parts.append("### 🔍 Issues Found\n")
            for i, issue in enumerate(review.issues, 1):
                severity_emoji = {
                    "critical": "🚨",
                    "high": "⚠️", 
                    "medium": "⚡",
                    "low": "💡"
                }.get(issue.severity.lower(), "📝")
                
                issue_text = f"{i}. {severity_emoji} **{issue.type.title()}** ({issue.severity})"
                if issue.line_range:
                    issue_text += f" - Lines {issue.line_range}"
                issue_text += f"\n   - **Issue:** {issue.description}\n   - **Suggestion:** {issue.suggestion}\n"
                comment_parts.append(issue_text)
        
        # Positive aspects
        if review.positive_aspects:
            comment_parts.append("### ✅ Positive Aspects\n")
            for aspect in review.positive_aspects:
                comment_parts.append(f"- {aspect}")
            comment_parts.append("")
        
        # Recommendations
        if review.recommendations:
            comment_parts.append("### 💡 Recommendations\n")
            for rec in review.recommendations:
                comment_parts.append(f"- {rec}")
            comment_parts.append("")
        
        # Approval status
        status_emoji = {
            "approved": "✅",
            "needs_changes": "🔄",
            "rejected": "❌"
        }.get(review.approval_status.lower(), "📝")
        
        comment_parts.append(f"### {status_emoji} Status: {review.approval_status.replace('_', ' ').title()}")
        
        return "\n".join(comment_parts)
    
    def review_code(self, diff: str, external_knowledge: str = "") -> str:
        """
        Main method: Perform complete multi-step code review
        """
        try:
            # Step 1: Analyze changes
            analysis = self._analyze_code_changes(diff)
            
            # Step 2: Detect issues
            issues = self._detect_issues(diff, analysis, external_knowledge)
            
            # Step 3: Generate structured review
            structured_review = self._generate_structured_review(diff, analysis, issues, external_knowledge)
            
            # Step 4: Format as readable comment
            formatted_comment = self._format_review_comment(structured_review)
            
            return formatted_comment
            
        except Exception as e:
            return f"❌ Error during advanced code review: {e}"
    
    def get_structured_review(self, diff: str, external_knowledge: str = "") -> ReviewSummary:
        """
        Get structured review data (for programmatic use)
        """
        try:
            analysis = self._analyze_code_changes(diff)
            issues = self._detect_issues(diff, analysis, external_knowledge)
            return self._generate_structured_review(diff, analysis, issues, external_knowledge)
        except Exception as e:
            # Return error as structured format
            return ReviewSummary(
                overall_assessment=f"Error during review: {e}",
                issues=[],
                positive_aspects=[],
                recommendations=[],
                approval_status="error"
            )
