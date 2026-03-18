from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from tests.providers.utils import FakeResp
from webscout.search.engines.brave.base import BraveBase
from webscout.search.engines.brave.text import BraveTextSearch


class TestBraveBase(unittest.TestCase):
  def test_brave_base_uses_curl_cffi_session(self) -> None:
    session_mock = MagicMock()
    session_mock.headers = MagicMock()

    fingerprint = {"User-Agent": "test-agent", "Accept-Language": "en-US"}

    with patch("webscout.search.engines.brave.base.Session", return_value=session_mock) as mock_session:
      with patch("webscout.search.engines.brave.base.LitAgent") as mock_litagent:
        mock_litagent.return_value.generate_fingerprint.return_value = fingerprint

        brave = BraveBase(
          timeout=15,
          proxies={"https": "http://proxy.local:8080"},
          verify=False,
          impersonate="chrome131",
        )

    mock_session.assert_called_once_with(
      proxies={"https": "http://proxy.local:8080"},
      verify=False,
      timeout=15,
      impersonate="chrome131",
    )
    session_mock.headers.update.assert_called_once_with(fingerprint)
    self.assertIs(brave.session, session_mock)


class TestBraveTextSearch(unittest.TestCase):
    def test_run_parses_results_from_brave_html(self) -> None:
        html = """
        <html>
          <body>
            <main>
              <div class="result-content">
                <a href="https://example.com/article">
                  <span class="title search-snippet-title">Example Title</span>
                </a>
                <div class="snippet">
                  <div class="generic-snippet">Example body text</div>
                </div>
              </div>
            </main>
          </body>
        </html>
        """

        searcher = BraveTextSearch(timeout=10)

        with patch.object(searcher.session, "get", return_value=FakeResp(text=html)) as mock_get:
            results = searcher.run("webscout", max_results=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Example Title")
        self.assertEqual(results[0].href, "https://example.com/article")
        self.assertEqual(results[0].body, "Example body text")
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        self.assertEqual(call_kwargs["params"]["q"], "webscout")
        self.assertEqual(call_kwargs["params"]["source"], "web")
        self.assertEqual(call_kwargs["params"]["spellcheck"], "0")
        self.assertEqual(call_kwargs["params"]["offset"], "0")
        self.assertEqual(call_kwargs["params"]["safesearch"], "moderate")


if __name__ == "__main__":
    unittest.main()
