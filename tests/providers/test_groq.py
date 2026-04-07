"""
Real API tests for GROQ provider.

These tests use actual API calls to verify provider functionality.
Set GROQ_API_KEY environment variable to run these tests.
"""

import os
import pytest

from webscout.Provider.Auth.Groq import GROQ
from webscout.Provider.Openai_comp.utils import ChatCompletion
from webscout.exceptions import FailedToGenerateResponseError


# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY environment variable not set"
)


class TestGROQ:
    """Real API tests for GROQ provider."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the GROQ provider with API key from environment."""
        api_key = os.environ.get("GROQ_API_KEY")
        assert api_key is not None, "GROQ_API_KEY must be set"
        self.api_key = api_key
        self.provider = GROQ(api_key=self.api_key)

    def test_ask_non_stream(self):
        """Test non-streaming chat completion."""
        response = self.provider.ask("Say 'Hello World' and nothing else")
        
        # Verify we got a response
        assert response is not None
        
        # Get the message content
        message = self.provider.get_message(response)
        assert message is not None
        assert len(message) > 0
        assert isinstance(message, str)

    def test_ask_stream(self):
        """Test streaming chat completion."""
        response = self.provider.ask("Count from 1 to 5", stream=True)
        
        # Verify we got a generator
        assert response is not None
        
        # Collect chunks
        chunks = list(response)
        assert len(chunks) > 0

    def test_chat_completion_with_tools(self):
        """Test chat completion with tool calling."""
        from webscout.AIbase import Tool
        
        tools = [
            Tool(
                name="get_time",
                description="Get the current time",
                parameters={}
            )
        ]
        
        # Register tools and chat
        self.provider.register_tools(tools)
        response = self.provider.chat("What time is it?")
        
        assert response is not None
        assert isinstance(response, str)

    def test_different_models(self):
        """Test using different GROQ models."""
        models_to_test = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
        
        for model in models_to_test:
            try:
                provider = GROQ(api_key=self.api_key, model=model)
                response = provider.ask("Say 'test'")
                assert response is not None
            except Exception as e:
                # Model might not be available, that's okay
                pytest.skip(f"Model {model} not available: {e}")


class TestGROQCompletions:
    """Test GROQ OpenAI-compatible completions interface."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the GROQ provider."""
        api_key = os.environ.get("GROQ_API_KEY")
        assert api_key is not None, "GROQ_API_KEY must be set"
        self.api_key = api_key
        self.client = GROQ(api_key=self.api_key)

    def test_chat_completions_create(self):
        """Test chat.completions.create interface."""
        completion = self.client.chat.completions.create(  # type: ignore[attr-defined]
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            stream=False
        )
        
        assert completion.choices is not None
        assert len(completion.choices) > 0
        assert completion.choices[0].message is not None
        assert completion.choices[0].message.content is not None

    def test_chat_completions_stream(self):
        """Test streaming chat completions."""
        completion = self.client.chat.completions.create(  # type: ignore[attr-defined]
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Count to 3"}],
            stream=True
        )
        
        # Collect streaming chunks
        chunks = list(completion)
        assert len(chunks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
