import asyncio
import json
import unittest
from collections.abc import Generator as GeneratorType
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from tests.providers.utils import FakeResp

from webscout.Provider.AISEARCH import (
    AyeSoul,
    IAsk,
    Monica,
    PERPLEXED,
    Perplexity,
    webpilotai,
)
from webscout.AIbase import SearchResponse


class FakeStreamResp(FakeResp):
    """A mock response that supports the `with` protocol and streaming."""

    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        json_data: dict | None = None,
        headers: dict | None = None,
        content: bytes | None = None,
        iter_bytes: list[bytes] | None = None,
        reason: str = "OK",
    ):
        super().__init__(status_code=status_code, text=text, json_data=json_data, headers=headers)
        self.content = content if content is not None else self.text.encode("utf-8")
        self._iter_bytes = iter_bytes or [self.content]
        self.reason = reason

    @property
    def ok(self):
        return self.status_code < 400

    def iter_content(self, chunk_size=1024):
        for chunk in self._iter_bytes:
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestAISEARCHProviders(unittest.TestCase):
    def test_iask_create_url(self):
        ai = IAsk()
        url = ai.create_url("Climate change", mode="academic", detail_level="detailed")
        self.assertIn("mode=academic", url)
        self.assertIn("q=Climate+change", url)
        self.assertIn("options%5Bdetail_level%5D=detailed", url)

    def test_iask_format_html(self):
        ai = IAsk()
        html = "<h1>Title</h1><p>Paragraph</p><div class='footnotes'><li><a href='https://example.com'>Link</a></li></div>"
        out = ai.format_html(html)
        self.assertIn("**Title**", out)
        self.assertIn("Paragraph", out)
        self.assertIn("https://example.com", out)

    @patch("webscout.Provider.AISEARCH.iask_search.AsyncSession")
    def test_iask_search_non_stream(self, mock_async_session):
        # Mock async HTTP session and response
        response = MagicMock()
        response.status_code = 200
        response.reason = "OK"
        response.text = "<div id=\"text\"><p>Answer</p></div>"

        async def fake_get(*args, **kwargs):
            return response

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.side_effect = fake_get
        mock_async_session.return_value = mock_session

        ai = IAsk()
        result = ai.search("Hi")
        self.assertIsInstance(result, SearchResponse)
        self.assertIn("Answer", str(result))

    @patch("webscout.Provider.AISEARCH.iask_search.AsyncSession")
    def test_iask_search_stream(self, mock_async_session):
        response = MagicMock()
        response.status_code = 200
        response.reason = "OK"
        response.text = "<div id=\"text\"><p>Answer</p></div>"

        async def fake_get(*args, **kwargs):
            return response

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.side_effect = fake_get
        mock_async_session.return_value = mock_session

        ai = IAsk()
        gen = ai.search("Hi", stream=True)
        self.assertTrue(hasattr(gen, "__iter__"))
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Answer", result)

    @patch("webscout.Provider.AISEARCH.monica_search.requests.Session.post")
    def test_monica_search_non_stream(self, mock_post):
        # Simulate a response with JSON content
        payload = b'{"text":"Hello"}'
        mock_post.return_value = FakeStreamResp(content=payload)

        ai = Monica()
        result = ai.search("Hi")
        self.assertIsInstance(result, SearchResponse)
        self.assertIn("Hello", str(result))

    @patch("webscout.Provider.AISEARCH.monica_search.requests.Session.post")
    def test_monica_search_stream(self, mock_post):
        payload_chunks = [b'{"text":"He"}', b'{"text":"llo"}']
        mock_post.return_value = FakeStreamResp(iter_bytes=payload_chunks)

        ai = Monica()
        gen = ai.search("Hi", stream=True)
        self.assertTrue(hasattr(gen, "__iter__"))
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Hello", result)

    @patch("webscout.Provider.AISEARCH.webpilotai_search.requests.Session.post")
    def test_webpilotai_search_non_stream(self, mock_post):
        payload = b'{"data":{"content":"Hi"}}'
        mock_post.return_value = FakeStreamResp(content=payload)

        ai = webpilotai()
        result = ai.search("Hi")
        self.assertIsInstance(result, SearchResponse)
        self.assertIn("Hi", str(result))

    @patch("webscout.Provider.AISEARCH.webpilotai_search.requests.Session.post")
    def test_webpilotai_search_stream(self, mock_post):
        payload_chunks = [b'{"data":{"content":"He"}}', b'{"data":{"content":"llo"}}']
        mock_post.return_value = FakeStreamResp(iter_bytes=payload_chunks)

        ai = webpilotai()
        gen = ai.search("Hi", stream=True)
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Hello", result)

    @patch("webscout.Provider.AISEARCH.PERPLEXED_search.requests.Session.post")
    def test_perplexed_search_non_stream(self, mock_post):
        # Provide a mock response for PERPLEXED.
        payload = b'{"success": true, "answer": "Hello"}'
        mock_post.return_value = FakeStreamResp(content=payload)

        ai = PERPLEXED()
        result = ai.search("Hi")
        self.assertIsInstance(result, SearchResponse)
        self.assertIn("Hello", str(result))

    @patch("webscout.Provider.AISEARCH.PERPLEXED_search.requests.Session.post")
    def test_perplexed_search_stream(self, mock_post):
        payload_chunks = [
            b'{"success": true, "answer": "He"}',
            b'{"success": true, "answer": "llo"}',
        ]
        mock_post.return_value = FakeStreamResp(iter_bytes=payload_chunks)

        ai = PERPLEXED()
        gen = ai.search("Hi", stream=True)
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Hello", result)

    @patch("webscout.Provider.AISEARCH.Perplexity.requests.Session.post")
    def test_perplexity_search_non_stream(self, mock_post):
        payload = b'data: {"step_type": "FINAL", "content": {"answer": "Hello"}}\r\n\r\n'
        mock_post.return_value = FakeStreamResp(content=payload)

        ai = Perplexity()
        result = ai.search("Hi")
        self.assertIsInstance(result, SearchResponse)
        self.assertIn("Hello", str(result))

    @patch("webscout.Provider.AISEARCH.Perplexity.requests.Session.post")
    def test_perplexity_search_stream(self, mock_post):
        payload_chunks = [
            b'data: {"step_type": "FINAL", "content": {"answer": "He"}}\r\n\r\n',
            b'data: {"step_type": "FINAL", "content": {"answer": "Hello"}}\r\n\r\n',
        ]
        mock_post.return_value = FakeStreamResp(iter_bytes=payload_chunks)

        ai = Perplexity()
        gen = ai.search("Hi", stream=True)
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Hello", result)

    @patch("webscout.Provider.AISEARCH.ayesoul_search.aiohttp.ClientSession")
    def test_ayesoul_search_stream(self, mock_client_session):
        # Mock WebSocket session and messages
        class FakeWS:
            def __init__(self, messages):
                self._messages = messages

            async def send_str(self, *args, **kwargs):
                return None

            async def receive(self):
                if not self._messages:
                    return MagicMock(type=None)
                return self._messages.pop(0)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class FakeSession:
            def __init__(self, ws):
                self._ws = ws

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def ws_connect(self, *args, **kwargs):
                return self._ws

        # Create a sequence of websocket messages
        msg1 = MagicMock(type=aiohttp.WSMsgType.TEXT, data=json.dumps({"status": "SOUL XStream", "message": "Hello"}))
        msg2 = MagicMock(type=aiohttp.WSMsgType.TEXT, data=json.dumps({"status": "SOUL XOver", "message": ""}))

        fake_ws = FakeWS([msg1, msg2])
        fake_session = FakeSession(fake_ws)
        mock_client_session.return_value = fake_session

        ai = AyeSoul()
        gen = ai.search("Hi", stream=True)
        self.assertTrue(hasattr(gen, "__iter__"))
        result = "".join(str(x) for x in cast(GeneratorType[Any, Any, Any], gen))
        self.assertIn("Hello", result)


if __name__ == "__main__":
    unittest.main()
