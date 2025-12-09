import os

from dotenv import load_dotenv
load_dotenv()

import pytest

from openai import OpenAI
from anthropic import Anthropic

# Test environment variables
def test_env_vars():
    """
    Test that all required environment variables are properly set.
    Validates the presence of API keys and configuration for OpenAI,
    Anthropic, and non-standard LLM providers.
    """
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set"
    assert os.getenv("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY not set"
    assert os.getenv("MODEL_NAME"), "MODEL_NAME not set"
    assert os.getenv("API_BASE_URL"), "API_BASE_URL not set"
    assert os.getenv("API_KEY"), "API_KEY not set"

# Test LLM OpenAI
def test_openai():
    """
    Test OpenAI API integration with a simple chat completion request.
    Verifies that the OpenAI client can successfully communicate with the API
    and return a valid response.
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    response = client.responses.create(
        model="gpt-5-mini",
        input=[{"role": "user", "content": "Hello"}]
    )

    assert response.output_text is not None

# Test LLM Anthropic
def test_anthropic():
    """
    Test Anthropic (Claude) API integration with a simple message request.
    Verifies that the Anthropic client can successfully communicate with
    Claude API and return a valid response with content.
    """
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    message = client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
            ],
        model="claude-sonnet-4-5-20250929",
        )

    assert message.content is not None

# Test non-standard LLM provider
def test_non_standard_provider():
    """
    Test integration with non-standard LLM providers using OpenAI-compatible API.
    Verifies that custom API endpoints can be accessed using the OpenAI client
    with custom base URLs and API keys.
    """
    client = OpenAI(
        base_url=os.getenv("API_BASE_URL"),
        api_key=os.getenv("API_KEY"),
    )
    
    response = client.responses.create(
        model=os.getenv("MODEL_NAME"),
        input=[{"role": "user", "content": "Hello"}]
    )

    assert response.output_text is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
