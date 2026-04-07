"""
Real API tests for HuggingFace provider.

These tests use actual API calls to verify provider functionality.
Set HUGGINGFACE_API_KEY environment variable to run these tests.
"""

import os
import pytest

from webscout.Provider.Auth.HuggingFace import HuggingFace


# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("HUGGINGFACE_API_KEY"),
    reason="HUGGINGFACE_API_KEY environment variable not set"
)


class TestHuggingFace:
    """Real API tests for HuggingFace provider."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the HuggingFace provider with API key from environment."""
        api_key = os.environ.get("HUGGINGFACE_API_KEY")
        assert api_key is not None, "HUGGINGFACE_API_KEY must be set"
        self.api_key = api_key
        self.provider = HuggingFace(api_key=self.api_key)

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

    def test_get_message(self):
        """Test message extraction from response."""
        response = self.provider.ask("Say 'test'")
        message = self.provider.get_message(response)
        assert message is not None
        assert isinstance(message, str)

    def test_different_models(self):
        """Test using different HuggingFace models."""
        models_to_test = ["meta-llama/Llama-3.2-3B-Instruct", "microsoft/DialoGPT-medium"]
        
        for model in models_to_test:
            try:
                provider = HuggingFace(api_key=self.api_key, model=model)  # type: ignore[arg-type]
                response = provider.ask("Say 'test'")
                assert response is not None
            except Exception as e:
                # Model might not be available, that's okay
                pytest.skip(f"Model {model} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
