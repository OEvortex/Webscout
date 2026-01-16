"""Unit tests for Brave text search parsing."""

from __future__ import annotations

import unittest

from webscout.search.engines.brave.text import BraveTextSearch
from webscout.search.results import TextResult


class TestBraveTextParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = BraveTextSearch()

    def test_parse_html_with_sibling_snippet(self) -> None:
        html = """
        <html><body>
        <div class="result-content svelte-1rq4ngz">
          <a href="https://en.wikipedia.org/wiki/Artificial_intelligence">
            <div class="title search-snippet-title">Artificial intelligence - Wikipedia</div>
          </a>
        </div>
        <div class="snippet svelte-jmfu5f">
          <div class="generic-snippet svelte-1cwdgg3">Artificial intelligence (AI) is intelligence demonstrated by machines.</div>
        </div>
        </body></html>
        """
        results = self.engine._parse_results_from_html(html)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        r = results[0]
        self.assertIsInstance(r, TextResult)
        self.assertEqual(r.title, "Artificial intelligence - Wikipedia")
        self.assertEqual(r.href, "https://en.wikipedia.org/wiki/Artificial_intelligence")
        self.assertIn("Artificial intelligence (AI)", r.body)

    def test_parse_html_with_inline_snippet(self) -> None:
        html = """
        <html><body>
        <div class="result-content">
          <a href="https://example.com/example">
            <div class="title search-snippet-title">Example Title</div>
            <div class="generic-snippet">This is an inline snippet inside the container.</div>
          </a>
        </div>
        </body></html>
        """
        results = self.engine._parse_results_from_html(html)
        self.assertGreater(len(results), 0)
        r = results[0]
        self.assertEqual(r.body, "This is an inline snippet inside the container.")

    def test_run_uses_session_get_and_parses(self) -> None:
        # Simulate a network response by swapping the engine's session.get
        html = """
        <html><body>
        <div class="result-content">
          <a href="https://example.com/example2">
            <div class="title search-snippet-title">Example2</div>
          </a>
        </div>
        <div class="snippet"><div class="generic-snippet">Snippet for example2.</div></div>
        </body></html>
        """

        class FakeResp:
            def __init__(self, text):
                self.text = text
            def raise_for_status(self):
                return None

        def fake_get(url, params=None, headers=None, timeout=None):
            return FakeResp(html)

        # patch session.get
        self.engine.session.get = fake_get  # type: ignore[assignment]

        results = self.engine.run("hi", max_results=1)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].title, "Example2")
        self.assertIn("Snippet for example2.", results[0].body)


if __name__ == "__main__":
    unittest.main()
