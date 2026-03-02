import json
import os
import tempfile
import unittest
from typing import Any, Dict, cast
from unittest.mock import MagicMock, patch

from webscout.Provider.Gemini import GEMINI


class TestGEMINI(unittest.TestCase):
    def setUp(self):
        # Create a dummy cookie file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cookie_file = os.path.join(self.temp_dir.name, "cookies.json")
        with open(self.cookie_file, "w") as f:
            f.write("dummy cookies")

        # Patch Chatbot to avoid actual network calls during init
        with patch('webscout.Provider.Gemini.Chatbot') as mock_chatbot:
            mock_chatbot.return_value.secure_1psid = "test_id"
            mock_chatbot.return_value.secure_1psidts = "test_ts"
            self.provider = GEMINI(cookie_file=self.cookie_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ask_non_stream(self):
        # Mock Chatbot.ask
        mock_response = {
            "content": "Hello from Gemini!",
            "conversation_id": "conv_123",
            "response_id": "resp_456",
            "choices": [{"content": ["Hello from Gemini!"]}],
            "images": [],
            "error": False
        }
        # Cast session to MagicMock for type checker
        mock_session = cast(MagicMock, self.provider.session)
        mock_session.ask.return_value = mock_response

        response = self.provider.ask("Hi")

        # Cast response to dict for type checker
        response_dict = cast(Dict[str, Any], response)
        self.assertEqual(response_dict["content"], "Hello from Gemini!")
        mock_session.ask.assert_called_once()

    def test_get_message(self):
        mock_response = {"content": "Test message"}
        message = self.provider.get_message(mock_response)
        self.assertEqual(message, "Test message")

if __name__ == "__main__":
    unittest.main()
