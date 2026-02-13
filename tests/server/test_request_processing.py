"""Tests for server request parameter preparation compatibility behavior."""

import unittest

from webscout.server.request_models import (
    ChatCompletionRequest,
    ImagePart,
    ImageURL,
    Message,
    TextPart,
)
from webscout.server.request_processing import prepare_provider_params, process_messages


class TestPrepareProviderParams(unittest.TestCase):
    def test_toolbaz_compat_normalizes_multimodal_and_filters_params(self) -> None:
        chat_request = ChatCompletionRequest(
            model="Toolbaz/gpt-5.2",
            stream=True,
            temperature=0.7,
            top_p=0.9,
            max_tokens=256,
            presence_penalty=0.2,
            frequency_penalty=0.2,
            stop=["END"],
            user="tester",
            messages=[
                Message(
                    role="user",
                    content=[
                        TextPart(type="text", text="Hello"),
                        ImagePart(
                            type="image_url",
                            image_url=ImageURL(url="https://example.com/image.png"),
                        ),
                    ],
                ),
                Message(role="assistant", content=None),
            ],
        )

        processed_messages = process_messages(chat_request.messages)
        params = prepare_provider_params(chat_request, "gpt-5.2", processed_messages, "Toolbaz")

        self.assertEqual(params["stream"], True)
        self.assertEqual(params["messages"][0]["content"], "Hello")
        self.assertEqual(params["messages"][1]["content"], "")

        self.assertIn("temperature", params)
        self.assertIn("top_p", params)
        self.assertIn("max_tokens", params)

        self.assertNotIn("presence_penalty", params)
        self.assertNotIn("frequency_penalty", params)
        self.assertNotIn("stop", params)
        self.assertNotIn("user", params)

    def test_default_behavior_keeps_extended_optional_params(self) -> None:
        chat_request = ChatCompletionRequest(
            model="SomeProvider/model",
            stream=False,
            temperature=0.5,
            presence_penalty=0.1,
            frequency_penalty=0.1,
            stop=["DONE"],
            user="abc",
            messages=[Message(role="user", content="Hi")],
        )

        processed_messages = process_messages(chat_request.messages)
        params = prepare_provider_params(chat_request, "model", processed_messages, "SomeProvider")

        self.assertEqual(params["messages"], processed_messages)
        self.assertEqual(params["stream"], False)
        self.assertIn("presence_penalty", params)
        self.assertIn("frequency_penalty", params)
        self.assertIn("stop", params)
        self.assertIn("user", params)


if __name__ == "__main__":
    unittest.main()
