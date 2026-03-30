import unittest
from typing import Any, Dict, cast
from unittest.mock import MagicMock, patch

from tests.providers.utils import FakeResp
from webscout.Provider.Auth.HuggingFace import HuggingFace


class TestHuggingFace(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        # Patch BackgroundModelFetcher to avoid async calls during init
        with patch('webscout.Provider.Auth.HuggingFace.BackgroundModelFetcher'):
            self.provider = HuggingFace(api_key=self.api_key)

    @patch('curl_cffi.requests.Session.post')
    def test_ask_non_stream(self, mock_post):
        # Mock response for non-streaming
        mock_response = FakeResp(
            json_data={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Hello from Hugging Face!"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        response = self.provider.ask("Hi")

        # HuggingFace.ask returns {"text": content}
        response_dict = cast(Dict[str, Any], response)
        self.assertEqual(response_dict["text"], "Hello from Hugging Face!")
        mock_post.assert_called_once()

    def test_get_message(self):
        mock_response = {"text": "Test message"}
        message = self.provider.get_message(mock_response)
        self.assertEqual(message, "Test message")

if __name__ == "__main__":
    unittest.main()
