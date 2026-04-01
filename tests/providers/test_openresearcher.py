"""Tests for OpenResearcher AI search provider."""

import json
from unittest import TestCase, mock

from curl_cffi.requests.exceptions import RequestException

from webscout.Provider.AISEARCH.openresearcher import OpenResearcher


class FakeResponse:
    """Mock response for testing."""

    def __init__(self, json_data=None, content=b"fake data", status_code=200):
        self._json_data = json_data or {}
        self.content = content
        self.status_code = status_code
        self.ok = status_code == 200

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")

    def iter_lines(self):
        """Simulate SSE events."""
        outputs = [
            '<div class="user-message">What is quantum computing?</div>',
            '<div class="user-message">What is quantum computing?</div><div class="round-badge">Round 1/5</div>',
            '<div class="user-message">What is quantum computing?</div><div class="round-badge">Round 1/5</div><div class="thought">Searching...</div>',
            '<div class="user-message">What is quantum computing?</div><div class="round-badge">Round 1/5</div><div class="thought">Searching...</div><div class="result">Quantum computing is...</div>',
        ]
        for output in outputs:
            data = ["", output, ""]
            yield f"data: {json.dumps(data)}".encode("utf-8")


class TestOpenResearcher(TestCase):
    """Test cases for OpenResearcher provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = OpenResearcher()

    def test_initialization(self):
        """Test provider initializes with correct defaults."""
        self.assertEqual(self.provider.default_max_rounds, 50)
        self.assertEqual(
            self.provider.serper_key,
            "b4ccaa60ac4905631ff4692ed09cf730bf9e9190",
        )
        self.assertEqual(self.provider.timeout, 120)
        self.assertEqual(self.provider.last_response, {})

    def test_custom_initialization(self):
        """Test provider initializes with custom parameters."""
        provider = OpenResearcher(
            timeout=60,
            serper_key="custom_key",
            max_rounds=10,
        )
        self.assertEqual(provider.timeout, 60)
        self.assertEqual(provider.serper_key, "custom_key")
        self.assertEqual(provider.default_max_rounds, 10)

    def test_required_auth(self):
        """Test that OpenResearcher doesn't require authentication."""
        self.assertFalse(self.provider.required_auth)

    def test_submit_research(self):
        """Test submitting research request."""
        mock_response = FakeResponse(json_data={"event_id": "test-event-123"})

        with mock.patch.object(self.provider.session, "post", return_value=mock_response):
            event_id = self.provider._submit_research(
                question="What is quantum computing?",
                serper_key="test_key",
                max_rounds=5,
            )

            self.assertEqual(event_id, "test-event-123")

    @mock.patch.object(OpenResearcher, "_submit_research", return_value="test-event-id")
    def test_search_non_streaming(self, mock_submit):
        """Test non-streaming search."""
        mock_response = FakeResponse()
        mock_response.ok = True

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            response = self.provider.search("What is AI?", stream=False)

            self.assertIsNotNone(response)
            self.assertIsInstance(response.text, str)

    @mock.patch.object(OpenResearcher, "_submit_research", return_value="test-event-id")
    def test_search_streaming(self, mock_submit):
        """Test streaming search."""
        mock_response = FakeResponse()
        mock_response.ok = True

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            chunks = list(self.provider.search("What is AI?", stream=True))

            self.assertGreater(len(chunks), 0)

    @mock.patch.object(OpenResearcher, "_submit_research", return_value="test-event-id")
    def test_search_raw(self, mock_submit):
        """Test raw search response."""
        mock_response = FakeResponse()
        mock_response.ok = True

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            response = self.provider.search("What is AI?", raw=True)

            self.assertIsInstance(response, str)

    @mock.patch.object(OpenResearcher, "_submit_research", return_value="test-event-id")
    def test_search_with_custom_rounds(self, mock_submit):
        """Test search with custom max rounds."""
        mock_response = FakeResponse()
        mock_response.ok = True

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            self.provider.search("What is AI?", max_rounds=10)

            mock_submit.assert_called_once()
            call_args = mock_submit.call_args
            self.assertEqual(call_args[1]["max_rounds"], 10)

    @mock.patch.object(OpenResearcher, "_submit_research", return_value="test-event-id")
    def test_search_with_custom_serper_key(self, mock_submit):
        """Test search with custom Serper key."""
        mock_response = FakeResponse()
        mock_response.ok = True

        with mock.patch.object(self.provider.session, "get", return_value=mock_response):
            self.provider.search("What is AI?", serper_key="custom_key")

            mock_submit.assert_called_once()
            call_args = mock_submit.call_args
            self.assertEqual(call_args[1]["serper_key"], "custom_key")

    @mock.patch.object(
        OpenResearcher,
        "_submit_research",
        side_effect=RequestException("API Error"),
    )
    def test_search_api_error(self, mock_submit):
        """Test search handles API errors gracefully."""
        from webscout import exceptions

        with self.assertRaises(exceptions.APIConnectionError):
            self.provider.search("What is AI?")
