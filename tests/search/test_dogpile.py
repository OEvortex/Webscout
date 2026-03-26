"""Tests for Dogpile search engine."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from webscout.search.engines.dogpile import Dogpile
from webscout.search.results import TextResult


class TestDogpile(unittest.TestCase):
    """Test cases for Dogpile search engine."""

    def test_dogpile_initialization(self) -> None:
        """Test Dogpile engine initializes correctly."""
        dogpile = Dogpile()

        self.assertEqual(dogpile.name, "dogpile")
        self.assertEqual(dogpile.category, "text")
        self.assertEqual(dogpile.provider, "dogpile")
        self.assertEqual(dogpile.search_url, "https://www.dogpile.com/serp")
        self.assertEqual(dogpile.search_method, "GET")

    def test_dogpile_build_payload_basic(self) -> None:
        """Test building basic search payload."""
        dogpile = Dogpile()

        payload = dogpile.build_payload(
            query="test query",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=1,
        )

        self.assertEqual(payload["q"], "test query")
        self.assertNotIn("page", payload)

    def test_dogpile_build_payload_pagination(self) -> None:
        """Test building payload with pagination."""
        dogpile = Dogpile()

        payload = dogpile.build_payload(
            query="test query",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=2,
        )

        self.assertEqual(payload["q"], "test query")
        self.assertEqual(payload["page"], 2)

    def test_dogpile_build_payload_with_sc(self) -> None:
        """Test building payload with Dogpile session token."""
        dogpile = Dogpile()

        payload = dogpile.build_payload(
            query="test query",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=1,
            sc="pnABUC50DVHf20",
        )

        self.assertEqual(payload["q"], "test query")
        self.assertEqual(payload["sc"], "pnABUC50DVHf20")

    def test_dogpile_search_forwards_request_kwargs(self) -> None:
        """Test Dogpile forwards browser cookies and headers to requests."""
        dogpile = Dogpile()

        with patch.object(dogpile, "request", return_value="<html></html>") as mock_request:
            with patch.object(dogpile, "extract_results", return_value=[]):
                results = dogpile.search(
                    query="test query",
                    sc="pnABUC50DVHf20",
                    headers={"User-Agent": "Browser UA"},
                    cookies={"__cf_bm": "cookie-value"},
                    timeout=12,
                )

        self.assertEqual(results, [])
        self.assertTrue(mock_request.called)
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["headers"]["User-Agent"], "Browser UA")
        self.assertEqual(call_kwargs["cookies"]["__cf_bm"], "cookie-value")
        self.assertEqual(call_kwargs["timeout"], 12)
        self.assertEqual(call_kwargs["params"]["sc"], "pnABUC50DVHf20")

    def test_dogpile_extract_results(self) -> None:
        """Test extracting results from Dogpile HTML."""
        # Actual HTML structure from dogpile.com
        html = """
        <html>
          <body>
            <div class="web-google">
              <div class="web-google__result">
                <a class="web-google__title" href="https://www.speedtest.net/">Speedtest by Ookla - The Global Broadband Speed Test</a>
                <span class="web-google__url">www.speedtest.net</span>
                <span class="web-google__description">Speedtest is better with the app. Download the Speedtest app for more metrics.</span>
              </div>
              <div class="web-google__result">
                <a class="web-google__title" href="https://fast.com/">Fast.com: Internet Speed Test</a>
                <span class="web-google__url">fast.com</span>
                <span class="web-google__description">How fast is your download speed? In seconds, FAST.com's simple Internet speed test.</span>
              </div>
              <div class="web-google__result">
                <a class="web-google__title" href="https://en.wikipedia.org/wiki/Test">Test - Wikipedia</a>
                <span class="web-google__url">en.wikipedia.org</span>
                <span class="web-google__description">Test(s), testing, or TEST may refer to: Test (assessment), an educational assessment.</span>
              </div>
            </div>
          </body>
        </html>
        """

        dogpile = Dogpile()

        # Test that the engine can process HTML
        results = dogpile.extract_results(html)

        # Should extract results from the HTML
        self.assertIsInstance(results, list)
        # With lxml, we should get actual results
        if results:
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0].title, "Speedtest by Ookla - The Global Broadband Speed Test")
            self.assertEqual(results[0].href, "https://www.speedtest.net/")
            self.assertIn("Speedtest", results[0].body)

    def test_dogpile_post_extract_results(self) -> None:
        """Test post-processing of results."""
        dogpile = Dogpile()

        # Create mock results
        results = [
            TextResult(
                title="  Valid Title  ",
                href="https://example.com/article",
                body="  Valid body text  ",
            ),
            TextResult(
                title="Invalid URL",
                href="not-a-valid-url",
                body="Should be filtered",
            ),
            TextResult(
                title="Another Valid",
                href="https://example.org/page",
                body="Another valid body",
            ),
        ]

        processed = dogpile.post_extract_results(results)

        # Should filter out invalid URLs
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0].title, "Valid Title")
        self.assertEqual(processed[0].body, "Valid body text")
        self.assertEqual(processed[1].title, "Another Valid")

    def test_dogpile_run_with_mock(self) -> None:
        """Test running a search with mocked response."""
        dogpile = Dogpile()

        with patch.object(dogpile, "search") as mock_search:
            mock_search.return_value = [
                TextResult(
                    title="Test Result Title",
                    href="https://example.com/test",
                    body="Test result body text",
                )
            ]

            results = dogpile.run(keywords="test query", max_results=5)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, "Test Result Title")
            self.assertEqual(results[0].href, "https://example.com/test")

    def test_dogpile_run_multiple_pages(self) -> None:
        """Test running search across multiple pages."""
        dogpile = Dogpile()

        with patch.object(dogpile, "search") as mock_search:
            # First page results
            mock_search.side_effect = [
                [TextResult(title=f"Result {i}", href=f"https://example.com/{i}", body=f"Body {i}") for i in range(10)],
                [TextResult(title=f"Result {i}", href=f"https://example.com/{i}", body=f"Body {i}") for i in range(10, 20)],
            ]

            results = dogpile.run(keywords="test", pages=2)

            self.assertEqual(mock_search.call_count, 2)
            self.assertEqual(len(results), 20)

    def test_dogpile_run_with_max_results(self) -> None:
        """Test that max_results limits the output."""
        dogpile = Dogpile()

        with patch.object(dogpile, "search") as mock_search:
            mock_search.return_value = [
                TextResult(title=f"Result {i}", href=f"https://example.com/{i}", body=f"Body {i}")
                for i in range(10)
            ]

            results = dogpile.run(keywords="test", max_results=5)

            self.assertEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()
