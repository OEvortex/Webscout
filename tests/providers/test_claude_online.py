import unittest
from typing import Any, Dict, cast
from unittest.mock import MagicMock, patch

from tests.providers.utils import FakeResp
from webscout.Provider.ClaudeOnline import ClaudeOnline


class TestClaudeOnline(unittest.TestCase):
    def setUp(self):
        # Patch LitAgent to avoid actual network calls during init
        with patch('webscout.Provider.ClaudeOnline.LitAgent'):
            self.provider = ClaudeOnline()

    @patch('curl_cffi.requests.Session.post')
    def test_ask_non_stream(self, mock_post):
        # Mock response for non-streaming (API response)
        mock_response = FakeResp(
            json_data={
                "message": {
                    "role": "assistant",
                    "content": "Hello from Claude Online!"
                }
            }
        )
        mock_post.return_value = mock_response

        response = self.provider.ask("Hi")

        # ClaudeOnline.ask returns {"text": content}
        response_dict = cast(Dict[str, Any], response)
        self.assertEqual(response_dict["text"], "Hello from Claude Online!")
        mock_post.assert_called_once()

    def test_get_message(self):
        mock_response = {
            "text": "Test message"
        }
        message = self.provider.get_message(mock_response)
        self.assertEqual(message, "Test message")

if __name__ == "__main__":
    unittest.main()
