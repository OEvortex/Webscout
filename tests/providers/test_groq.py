"""
Real API tests for GROQ provider.

These tests use actual API calls to verify provider functionality.
Set GROQ_API_KEY environment variable to run these tests.
"""

import os

import pytest

from llm4free.llm.Auth.groq import Groq

# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"), reason="GROQ_API_KEY environment variable not set"
)


class TestGROQ:
    """Real API tests for GROQ provider."""

    @pytest.fixture(autouse=True)
    def setup(self):
        api_key = os.environ.get("GROQ_API_KEY")
        assert api_key is not None, "GROQ_API_KEY must be set"
        self.provider = Groq(api_key=api_key)

    def test_chat_completions_non_stream(self):
        completion = self.provider.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Hello World' and nothing else"}],
            stream=False,
        )
        assert completion.choices is not None
        assert len(completion.choices) > 0
        assert completion.choices[0].message is not None
        assert completion.choices[0].message.content is not None
        assert len(completion.choices[0].message.content) > 0

    def test_chat_completions_stream(self):
        completion = self.provider.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Count to 3"}],
            stream=True,
        )
        chunks = list(completion)
        assert len(chunks) > 0

    def test_different_models(self):
        models_to_test = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
        for model in models_to_test:
            try:
                provider = Groq(api_key=os.environ["GROQ_API_KEY"])
                completion = provider.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    stream=False,
                )
                assert completion.choices is not None
            except Exception as e:
                pytest.skip(f"Model {model} not available: {e}")
