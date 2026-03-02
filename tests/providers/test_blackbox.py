import unittest
from typing import Any, Dict, cast
from unittest.mock import MagicMock, patch

from tests.providers.utils import FakeResp
from webscout.Provider.blackbox import Blackbox


class TestBlackbox(unittest.TestCase):
    def setUp(self):
        # Patch BackgroundModelFetcher to avoid async calls during init
        with patch('webscout.Provider.blackbox.BackgroundModelFetcher'):
            self.provider = Blackbox()

    @patch('curl_cffi.requests.Session.post')
    def test_ask_non_stream(self, mock_post):
        # Mock response for non-streaming
        mock_response = FakeResp(
            json_data={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Hello from Blackbox!"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        response = self.provider.ask("Hi")

        # Blackbox.ask returns {"text": content}
        response_dict = cast(Dict[str, Any], response)
        self.assertEqual(response_dict["text"], "Hello from Blackbox!")
        mock_post.assert_called_once()

    def test_get_message(self):
        mock_response = {"text": "Test message"}
        message = self.provider.get_message(mock_response)
        self.assertEqual(message, "Test message")

if __name__ == "__main__":
    unittest.main()
