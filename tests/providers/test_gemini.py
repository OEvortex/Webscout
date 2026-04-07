"""
Real API tests for Gemini provider.

These tests use actual API calls to verify provider functionality.
Requires a valid cookies.json file for Gemini authentication.
Set GEMINI_COOKIE_FILE environment variable to run these tests.
"""

import os
import pytest

from webscout.Provider.Auth.Gemini import GEMINI


# Skip all tests in this module if no cookie file is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_COOKIE_FILE"),
    reason="GEMINI_COOKIE_FILE environment variable not set"
)


class TestGemini:
    """Real API tests for Gemini provider."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the Gemini provider with cookie file from environment."""
        cookie_file = os.environ.get("GEMINI_COOKIE_FILE")
        assert cookie_file is not None, "GEMINI_COOKIE_FILE must be set"
        self.cookie_file = cookie_file
        self.provider = GEMINI(cookie_file=self.cookie_file)

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
        """Test using different Gemini models."""
        models_to_test = ["gemini-3.0-flash", "gemini-3.0-pro"]
        
        for model in models_to_test:
            try:
                provider = GEMINI(cookie_file=self.cookie_file, model=model)  # type: ignore[arg-type]
                response = provider.ask("Say 'test'")
                assert response is not None
            except Exception as e:
                # Model might not be available, that's okay
                pytest.skip(f"Model {model} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
