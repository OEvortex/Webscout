import unittest
from typing import Any, Dict, cast
from unittest.mock import patch

from tests.providers.utils import FakeResp
from webscout.Provider.AvaSupernova import AvaSupernova
from webscout.Provider.Openai_comp.avasupernova import AvaSupernova as OpenAIAvaSupernova
from webscout.Provider.Openai_comp.utils import ChatCompletion


class TestAvaSupernova(unittest.TestCase):
    def test_ask_non_stream(self):
        provider = AvaSupernova()

        # Mock response for non-streaming
        mock_response = FakeResp(
            json_data={
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello from Ava Supernova!"}}
                ]
            }
        )

        with patch("curl_cffi.requests.Session.post", return_value=mock_response):
            response = provider.ask("Hi")

        response_dict = cast(Dict[str, Any], response)
        self.assertEqual(response_dict["text"], "Hello from Ava Supernova!")


class TestOpenAIAvaSupernova(unittest.TestCase):
    def test_chat_completion_non_stream(self):
        client = OpenAIAvaSupernova()

        mock_response = FakeResp(
            json_data={
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello from OpenAI-compatible Ava Supernova!"}}
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        )

        with patch("curl_cffi.requests.Session.post", return_value=mock_response):
            completion = client.chat.completions.create(
                model="glm-4.5-flash", messages=[{"role": "user", "content": "Hi"}], stream=False
            )

        # Cast to ChatCompletion to help type checker understand this is not a generator
        completion = cast(ChatCompletion, completion)
        assert completion.choices[0].message is not None
        self.assertEqual(completion.choices[0].message.content, "Hello from OpenAI-compatible Ava Supernova!")


if __name__ == "__main__":
    unittest.main()
