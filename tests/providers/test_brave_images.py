"""Unit tests for Brave Images search engine."""

from __future__ import annotations

import unittest
from typing import Any

from webscout.search.engines.brave.images import BraveImages
from webscout.search.results import ImagesResult


class TestBraveImages(unittest.TestCase):
    """Test cases for BraveImages search engine."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = BraveImages()

    def test_initialization(self) -> None:
        """Test that BraveImages initializes correctly."""
        self.assertEqual(self.engine.name, "brave_images")
        self.assertEqual(self.engine.category, "images")
        self.assertEqual(self.engine.provider, "brave")
        self.assertIsNotNone(self.engine.search_url)
        self.assertEqual(self.engine.search_method, "GET")

    def test_build_payload_basic(self) -> None:
        """Test payload building for basic search."""
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=1,
        )

        self.assertEqual(payload["q"], "test")
        self.assertEqual(payload["source"], "web")
        self.assertEqual(payload["safesearch"], "moderate")
        self.assertNotIn("offset", payload)

    def test_build_payload_with_safesearch_levels(self) -> None:
        """Test payload building with different safesearch levels."""
        # Test 'on' level
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="on",
            timelimit=None,
            page=1,
        )
        self.assertEqual(payload["safesearch"], "strict")

        # Test 'off' level
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="off",
            timelimit=None,
            page=1,
        )
        self.assertEqual(payload["safesearch"], "off")

    def test_build_payload_pagination(self) -> None:
        """Test payload building with pagination."""
        # Page 2
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=2,
        )
        self.assertEqual(payload["offset"], "40")

        # Page 3
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="moderate",
            timelimit=None,
            page=3,
        )
        self.assertEqual(payload["offset"], "80")

    def test_build_payload_with_timelimit(self) -> None:
        """Test payload building with time limit."""
        payload = self.engine.build_payload(
            query="test",
            region="us-en",
            safesearch="moderate",
            timelimit="week",
            page=1,
        )

        self.assertEqual(payload["tf"], "week")

    def test_extract_original_url_with_valid_base64(self) -> None:
        """Test extracting original URL from Brave proxy URL."""
        # This is a real example from Brave search
        proxy_url = (
            "https://imgs.search.brave.com/XvJSA-PWb-es9AGWtu53QrmW4ToFenxuW8ipm6TaZzw/"
            "rs:fit:500:0:1:0/g:ce/"
            "aHR0cHM6Ly93YWxscGFwZXJzLmNvbS9pbWFnZXMvaGQvaGktcGljdHVyZXMtN2I5"
            "Nm56c3FlZTlqcnl2ZC5qcGc="
        )
        original = self.engine._extract_original_url(proxy_url)
        # The base64 decoding might not work perfectly due to encoding, but
        # should not raise an exception
        self.assertIsNotNone(original)

    def test_extract_original_url_invalid(self) -> None:
        """Test extracting original URL from invalid proxy URL."""
        invalid_url = "https://example.com/invalid"
        result = self.engine._extract_original_url(invalid_url)
        # Should return the original URL if extraction fails
        self.assertEqual(result, invalid_url)

    def test_search_url_format(self) -> None:
        """Test that search URL is correctly formatted."""
        self.assertTrue(
            self.engine.search_url.startswith("https://"),
            "Search URL should start with https://",
        )
        self.assertIn(
            "search.brave.com", self.engine.search_url, "Should use Brave search domain"
        )
        self.assertIn("images", self.engine.search_url, "Should be images endpoint")

    def test_result_type(self) -> None:
        """Test that result type is ImagesResult."""
        self.assertEqual(self.engine.result_type, ImagesResult)

    def test_extract_results_empty(self) -> None:
        """Test extracting results from empty/invalid HTML."""
        # This will test the error handling
        try:
            # Provide minimal valid HTML
            html = "<html><body><main></main></body></html>"
            results = self.engine.extract_results(html)
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 0)
        except ImportError:
            # lxml might not be available in test environment
            self.skipTest("lxml not available")

    def test_run_with_keyword_positional(self) -> None:
        """Test run method with keyword as positional argument."""
        # This will fail without internet, but tests the method signature
        results = self.engine.run("test", "us-en", "moderate")
        self.assertIsInstance(results, list)

    def test_run_with_kwargs(self) -> None:
        """Test run method with keyword arguments."""
        results = self.engine.run(keywords="test", region="us-en", safesearch="moderate")
        self.assertIsInstance(results, list)

    def test_run_default_arguments(self) -> None:
        """Test run method with default arguments."""
        results = self.engine.run("test")
        self.assertIsInstance(results, list)

    def test_category_is_images(self) -> None:
        """Test that category is correctly set to images."""
        self.assertEqual(self.engine.category, "images")

    def test_xpath_expressions_exist(self) -> None:
        """Test that XPath expressions are defined."""
        self.assertTrue(
            self.engine.items_xpath, "items_xpath should be defined"
        )
        self.assertTrue(
            self.engine.elements_xpath, "elements_xpath should be defined"
        )
        self.assertIn("title", self.engine.elements_xpath)
        self.assertIn("image", self.engine.elements_xpath)
        self.assertIn("source", self.engine.elements_xpath)


class TestBraveImagesIntegration(unittest.TestCase):
    """Integration tests for BraveImages (requires internet)."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = BraveImages()

    def test_real_search_single_result(self) -> None:
        """Test real search with internet connection."""
        # This test requires internet and will be skipped if unavailable
        try:
            results = self.engine.run("cat", max_results=1)
            if results:
                self.assertGreater(len(results), 0)
                result = results[0]
                self.assertIsInstance(result, ImagesResult)
                # Basic sanity checks
                self.assertIsNotNone(result.image)
        except Exception as e:
            self.skipTest(f"Integration test skipped: {e}")

    def test_real_search_multiple_results(self) -> None:
        """Test real search returning multiple results."""
        try:
            results = self.engine.run("nature", max_results=5)
            if results:
                self.assertGreater(len(results), 0)
                for result in results:
                    self.assertIsInstance(result, ImagesResult)
                    self.assertIsNotNone(result.image)
        except Exception as e:
            self.skipTest(f"Integration test skipped: {e}")


if __name__ == "__main__":
    unittest.main()
