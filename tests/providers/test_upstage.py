"""Unit tests for Upstage Provider."""

import json
import unittest
from unittest.mock import MagicMock, patch

from webscout import exceptions
from webscout.Provider.Upstage import Upstage


class FakeResp:
    """Fake response object for testing."""

    def __init__(self, status_code: int, json_data: dict, text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        if not self._json:
            raise json.JSONDecodeError("No JSON", "", 0)
        return self._json

    def iter_content(self, chunk_size=None):
        """Simulate streaming response."""
        return iter([])


class TestUpstageProvider(unittest.TestCase):
    """Test cases for Upstage provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key-12345"

    def test_initialization_with_api_key(self):
        """Test provider initialization with API key."""
        provider = Upstage(api_key=self.api_key)
        assert provider.api_key == self.api_key
        assert provider.model == "solar-pro-3"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 4096

    def test_initialization_without_api_key_raises_error(self):
        """Test that initialization without API key raises AuthenticationError."""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(exceptions.AuthenticationError):
                Upstage(api_key=None)

    def test_invalid_model_raises_error(self):
        """Test that invalid model raises ValueError."""
        with self.assertRaises(ValueError):
            Upstage(api_key=self.api_key, model="invalid-model")

    def test_valid_models(self):
        """Test that all valid models are acceptable."""
        for model in Upstage.AVAILABLE_MODELS:
            provider = Upstage(api_key=self.api_key, model=model)
            assert provider.model == model

    def test_upstage_extractor_valid_response(self):
        """Test content extraction from valid SSE response."""
        chunk_json = {
            "choices": [
                {"delta": {"content": "Hello world"}}
            ]
        }
        result = Upstage._upstage_extractor(chunk_json)
        assert result == "Hello world"

    def test_upstage_extractor_empty_content(self):
        """Test that extractor returns empty string for empty content."""
        chunk_json = {
            "choices": [
                {"delta": {"content": ""}}
            ]
        }
        result = Upstage._upstage_extractor(chunk_json)
        assert result == ""

    def test_upstage_extractor_no_choices(self):
        """Test that extractor returns None when no choices."""
        chunk_json = {"choices": []}
        result = Upstage._upstage_extractor(chunk_json)
        assert result is None

    def test_upstage_extractor_invalid_json(self):
        """Test that extractor returns None for invalid JSON."""
        result = Upstage._upstage_extractor("invalid")
        assert result is None

    def test_get_message_with_dict_response(self):
        """Test extracting message from dict response."""
        provider = Upstage(api_key=self.api_key)
        response = {"text": "Hello world"}
        result = provider.get_message(response)
        assert result == "Hello world"

    def test_get_message_with_string_response(self):
        """Test extracting message from string response."""
        provider = Upstage(api_key=self.api_key)
        response = "Direct string response"
        result = provider.get_message(response)
        assert result == "Direct string response"

    def test_get_message_with_empty_response(self):
        """Test handling of empty response."""
        provider = Upstage(api_key=self.api_key)
        response = {"missing_key": "value"}
        result = provider.get_message(response)
        assert result == ""

    @patch("webscout.Provider.Upstage.requests.Session.post")
    def test_non_stream_success(self, mock_post):
        """Test successful non-streaming request."""
        mock_response = FakeResp(
            status_code=200,
            json_data={
                "choices": [
                    {
                        "message": {"content": "This is a test response"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        provider = Upstage(api_key=self.api_key)
        result = provider.ask("Test prompt", stream=False)

        assert isinstance(result, dict)
        assert (result.get("text") == "This is a test response")  # type: ignore

    @patch("webscout.Provider.Upstage.requests.Session.post")
    def test_non_stream_api_error(self, mock_post):
        """Test handling of API errors in non-streaming mode."""
        mock_response = FakeResp(
            status_code=401,
            json_data={"error": {"message": "Invalid API key"}},
            text="Unauthorized"
        )
        mock_post.return_value = mock_response

        provider = Upstage(api_key=self.api_key)

        with self.assertRaises(exceptions.FailedToGenerateResponseError):
            provider.ask("Test prompt", stream=False)

    @patch("webscout.Provider.Upstage.requests.Session.post")
    def test_chat_returns_string(self, mock_post):
        """Test that chat returns string when not streaming."""
        mock_response = FakeResp(
            status_code=200,
            json_data={
                "choices": [
                    {
                        "message": {"content": "Chat response"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        provider = Upstage(api_key=self.api_key)
        result = provider.chat("Chat test", stream=False)

        assert isinstance(result, str)
        assert result == "Chat response"

    def test_required_auth_flag(self):
        """Test that Upstage requires authentication."""
        assert Upstage.required_auth is True

    def test_available_models_list(self):
        """Test that available models are properly defined."""
        assert len(Upstage.AVAILABLE_MODELS) >= 3
        assert "solar-pro-3" in Upstage.AVAILABLE_MODELS
        assert "solar-pro-2" in Upstage.AVAILABLE_MODELS
        assert "solar-1-pro" in Upstage.AVAILABLE_MODELS

    @patch("webscout.Provider.Upstage.requests.Session.post")
    def test_conversation_history_update(self, mock_post):
        """Test that conversation history is updated."""
        mock_response = FakeResp(
            status_code=200,
            json_data={
                "choices": [
                    {
                        "message": {"content": "Response"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        provider = Upstage(
            api_key=self.api_key,
            is_conversation=True
        )
        initial_history = provider.conversation.chat_history

        provider.chat("Test", stream=False, conversationally=True)

        # History should be updated
        assert len(provider.conversation.chat_history) >= len(initial_history)

    def test_custom_temperature(self):
        """Test provider initialization with custom temperature."""
        provider = Upstage(
            api_key=self.api_key,
            temperature=1.5
        )
        assert provider.temperature == 1.5

    def test_custom_max_tokens(self):
        """Test provider initialization with custom max tokens."""
        provider = Upstage(
            api_key=self.api_key,
            max_tokens=2048
        )
        assert provider.max_tokens == 2048

    def test_custom_system_message(self):
        """Test provider initialization with custom system message."""
        custom_message = "You are an expert programmer."
        provider = Upstage(
            api_key=self.api_key,
            system_message=custom_message
        )
        assert provider.system_message == custom_message


if __name__ == "__main__":
    unittest.main()
