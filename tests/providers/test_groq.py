import unittest
from typing import Any, Dict, cast
from unittest.mock import MagicMock, patch

from tests.providers.utils import FakeResp
from webscout.Provider.Groq import GROQ


class TestGROQ(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        # Patch BackgroundModelFetcher to avoid async calls during init
        with patch('webscout.Provider.Groq.BackgroundModelFetcher'):
            self.provider = GROQ(api_key=self.api_key)

    @patch('curl_cffi.requests.Session.post')
    def test_ask_non_stream(self, mock_post):
        # Mock response for non-streaming
        mock_response = FakeResp(
            json_data={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Hello from GROQ!"}
                    }
                ]
            }
        )
        mock_post.return_value = mock_response

        response = self.provider.ask("Hi")

        # Extract message using get_message
        message = self.provider.get_message(response)
        self.assertEqual(message, "Hello from GROQ!")
        mock_post.assert_called_once()

    @patch('curl_cffi.requests.Session.post')
    def test_ask_error_handling(self, mock_post):
        # Mock a 401 Unauthorized error
        mock_response = FakeResp(status_code=401, text="Unauthorized")
        mock_post.return_value = mock_response

        from webscout.exceptions import FailedToGenerateResponseError
        with self.assertRaises(FailedToGenerateResponseError):
            self.provider.ask("Hi")

if __name__ == "__main__":
    unittest.main()
