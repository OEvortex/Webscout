"""
Real API tests for OpenAI provider.

These tests use actual API calls to verify provider functionality.
Set OPENAI_API_KEY environment variable to run these tests.
"""

import os

import pytest

from llm4free.client import Client

# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set"
)


class TestOpenAI:
    """Real API tests for OpenAI via the unified Client."""

    @pytest.fixture(autouse=True)
    def setup(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        assert api_key is not None, "OPENAI_API_KEY must be set"
        self.client = Client(api_key=api_key)

    def test_chat_completions_non_stream(self):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World' and nothing else"}],
            stream=False,
        )
        assert response.choices is not None
        assert len(response.choices) > 0
        assert response.choices[0].message is not None
        assert response.choices[0].message.content is not None
        assert len(response.choices[0].message.content) > 0

    def test_chat_completions_stream(self):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Count to 3"}],
            stream=True,
        )
        chunks = list(response)
        assert len(chunks) > 0
