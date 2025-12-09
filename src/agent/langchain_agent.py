"""
LangChain Agent-based Code Review Agent with tools and structured output.
"""
import textwrap
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain.agents.structured_output import ToolStrategy
from langgraph.checkpoint.memory import MemorySaver


# Context Schema
class ReviewContext(BaseModel):
    """Context for code review session"""
    repository_name: str = Field(description="Name of the repository being reviewed")
    pull_request_id: str = Field(description="Pull request identifier")
    author: str = Field(description="Author of the code changes")
    external_knowledge: str = Field(default="", description="Additional project context")


# Response Format
class CodeReviewResponse(BaseModel):
    """Structured response format for code reviews"""
    summary: str = Field(description="Brief summary of the code review")
    detailed_analysis: str = Field(description="Detailed technical analysis")
    issues_found: List[str] = Field(description="List of issues identified")
    recommendations: List[str] = Field(description="List of recommendations")
    approval_status: str = Field(description="Approval status: approved, needs_changes, rejected")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0")


# Tools for the agent
@tool
def analyze_code_complexity(diff: str) -> str:
    """Analyze the complexity of code changes in a diff."""
    lines_added = diff.count('\n+')
    lines_removed = diff.count('\n-')
    files_changed = diff.count('--- a/')
    
    complexity_score = (lines_added + lines_removed) / max(files_changed, 1)
    
    if complexity_score > 50:
        complexity = "High"
    elif complexity_score > 20:
        complexity = "Medium"
    else:
        complexity = "Low"
    
    return f"Complexity Analysis: {complexity} ({complexity_score:.1f} lines per file). Files changed: {files_changed}, Lines added: {lines_added}, Lines removed: {lines_removed}"


@tool
def detect_security_patterns(diff: str) -> str:
    """Detect potential security issues in code diff."""
    security_patterns = {
        'sql_injection': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP'],
        'xss': ['innerHTML', 'document.write', 'eval('],
        'hardcoded_secrets': ['password', 'api_key', 'secret', 'token'],
        'unsafe_functions': ['exec(', 'eval(', 'system(', 'shell_exec']
    }
    
    issues = []
    diff_upper = diff.upper()
    
    for category, patterns in security_patterns.items():
        for pattern in patterns:
            if pattern.upper() in diff_upper:
                issues.append(f"Potential {category.replace('_', ' ')} risk: Found '{pattern}'")
    
    if issues:
        return "Security Analysis: " + "; ".join(issues)
    else:
        return "Security Analysis: No obvious security patterns detected"


@tool
def check_code_style(diff: str) -> str:
    """Check code style and formatting issues."""
    style_issues = []
    
    lines = diff.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('+'):
            # Check for common style issues
            if len(line) > 120:
                style_issues.append(f"Line {i+1}: Line too long (>120 chars)")
            if line.endswith(' '):
                style_issues.append(f"Line {i+1}: Trailing whitespace")
            if '\t' in line:
                style_issues.append(f"Line {i+1}: Tab character found (use spaces)")
    
    if style_issues:
        return "Style Analysis: " + "; ".join(style_issues[:5])  # Limit to 5 issues
    else:
        return "Style Analysis: No major style issues detected"


@tool
def suggest_improvements(diff: str) -> str:
    """Suggest general improvements for the code changes."""
    suggestions = []
    
    # Analyze patterns in the diff
    if 'def ' in diff:
        suggestions.append("Consider adding docstrings to new functions")
    if 'import ' in diff:
        suggestions.append("Ensure imports are organized and necessary")
    if 'TODO' in diff or 'FIXME' in diff:
        suggestions.append("Address TODO/FIXME comments before merging")
    if diff.count('\n+') > 100:
        suggestions.append("Large changes detected - consider breaking into smaller commits")
    
    if not suggestions:
        suggestions.append("Code changes look reasonable")
    
    return "Improvement Suggestions: " + "; ".join(suggestions)


class LangChainCodeReviewAgent:
    """LangChain Agent-based Code Review Agent with tools and structured output"""
    
    def __init__(self, llm_client: BaseChatModel, model_name: str):
        """
        Initialize LangChain code review agent
        Args:
            llm_client: LangChain LLM client
            model_name: Name of the model being used
        """
        self.llm_client = llm_client
        self.model_name = model_name
        
        # Define system prompt
        self.system_prompt = textwrap.dedent("""
        You are an expert code review agent with access to specialized analysis tools.
        
        Your role is to:
        1. Use the available tools to analyze code changes thoroughly
        2. Provide constructive, actionable feedback
        3. Focus on code quality, security, performance, and maintainability
        4. Give specific recommendations for improvement
        5. Provide a final approval status
        
        Always use the tools available to you for comprehensive analysis.
        Be professional, constructive, and helpful in your reviews.
        """).strip()
        
        # Create tools list
        self.tools = [
            analyze_code_complexity,
            detect_security_patterns,
            check_code_style,
            suggest_improvements
        ]
        
        # Create checkpointer for conversation memory
        self.checkpointer = MemorySaver()
        
        # Create the agent with structured output
        self.agent = create_agent(
            model=self.llm_client,
            system_prompt=self.system_prompt,
            tools=self.tools,
            context_schema=ReviewContext,
            response_format=ToolStrategy(CodeReviewResponse),
            checkpointer=self.checkpointer
        )
    
    def review_code(self, diff: str, context: ReviewContext, thread_id: str = "default") -> CodeReviewResponse:
        """
        Perform code review using LangChain agent with tools and structured output
        
        Args:
            diff: Code diff to review
            context: Review context information
            thread_id: Unique identifier for conversation thread
            
        Returns:
            Structured code review response
        """
        try:
            # Prepare the review request message
            review_request = f"""
            Please review this code diff using all available tools:
            
            Repository: {context.repository_name}
            PR ID: {context.pull_request_id}
            Author: {context.author}
            Additional Context: {context.external_knowledge}
            
            Code Diff:
            ```diff
            {diff}
            ```
            
            Please use your tools to analyze:
            1. Code complexity and maintainability
            2. Security vulnerabilities and risks
            3. Code style and formatting issues
            4. General improvement suggestions
            
            Provide a comprehensive structured review with specific findings and recommendations.
            """
            
            # Configure the agent execution
            config = {"configurable": {"thread_id": thread_id}}
            
            print("🤖 Executing LangChain agent with tools...")
            
            # Invoke the agent
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": review_request}]},
                config=config,
                context=context
            )
            
            print("✅ Agent execution completed!")
            
            # Return the structured response directly
            return response['structured_response']
            
        except Exception as e:
            print(f"❌ Agent execution failed: {e}")
            return CodeReviewResponse(
                summary=f"Error during review: {e}",
                detailed_analysis="Agent execution failed",
                issues_found=[str(e)],
                recommendations=["Please check the agent configuration"],
                approval_status="error",
                confidence_score=0.0
            )
    
    def _parse_agent_response(self, response: str, context: ReviewContext) -> CodeReviewResponse:
        """Parse agent response into structured format"""
        try:
            # Extract key information from the agent's response
            lines = response.split('\n')
            issues = []
            recommendations = []
            
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['issue', 'problem', 'bug', 'vulnerability']):
                    if line and not line.startswith('#'):
                        issues.append(line)
                elif any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                    if line and not line.startswith('#'):
                        recommendations.append(line)
            
            # Determine approval status
            if any(keyword in response.lower() for keyword in ['critical', 'severe', 'dangerous']):
                approval_status = "rejected"
                confidence = 0.95
            elif len(issues) > 2:
                approval_status = "needs_changes"
                confidence = 0.9
            elif len(issues) > 0:
                approval_status = "needs_changes"
                confidence = 0.85
            else:
                approval_status = "approved"
                confidence = 0.8
            
            return CodeReviewResponse(
                summary=f"Review completed for {context.repository_name} PR #{context.pull_request_id}. Found {len(issues)} issues.",
                detailed_analysis=response,
                issues_found=issues[:10],  # Limit to top 10
                recommendations=recommendations[:10],  # Limit to top 10
                approval_status=approval_status,
                confidence_score=confidence
            )
            
        except Exception as e:
            return CodeReviewResponse(
                summary=f"Error parsing response: {e}",
                detailed_analysis=response,
                issues_found=[f"Parse error: {e}"],
                recommendations=["Please check the agent response format"],
                approval_status="error",
                confidence_score=0.0
            )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return [tool.name for tool in self.tools]
    
    def continue_conversation(self, message: str, thread_id: str, context: ReviewContext) -> CodeReviewResponse:
        """Continue a conversation in the same thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
                context=context
            )
            
            return response['structured_response']
            
        except Exception as e:
            return CodeReviewResponse(
                summary=f"Error in conversation: {e}",
                detailed_analysis="Conversation failed",
                issues_found=[str(e)],
                recommendations=["Please check the agent configuration"],
                approval_status="error",
                confidence_score=0.0
            )
