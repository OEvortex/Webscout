"""Brave search engine implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from ..base import BaseSearchEngine
from ..results import TextResult


class Brave(BaseSearchEngine[TextResult]):
    """Brave search engine."""

    name = "brave"
    category = "text"
    provider = "brave"

    search_url = "https://search.brave.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-type='web']"
    elements_xpath: Mapping[str, str] = {
        "title": ".//div[(contains(@class,'title') or contains(@class,'sitename-container')) and position()=last()]//text()",
        "href": "./a/@href",
        "body": ".//div[contains(@class, 'description')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        safesearch_base = {"on": "strict", "moderate": "moderate", "off": "off"}
        payload = {
            "q": query,
            "source": "web",
            "safesearch": safesearch_base[safesearch.lower()],
        }
        if timelimit:
            payload["tf"] = timelimit
        if page > 1:
            payload["offset"] = f"{(page - 1) * 10}"
        return payload

    def run(self, *args, **kwargs) -> list[TextResult]:
        """Run text search on Brave.

        Args:
            keywords: Search query.
            region: Region code.
            safesearch: Safe search level.
            max_results: Maximum number of results (ignored for now).

        Returns:
            List of TextResult objects.
        """
        keywords = args[0] if args else kwargs.get("keywords")
        if keywords is None:
            keywords = ""
        region = args[1] if len(args) > 1 else kwargs.get("region", "us-en")
        safesearch = args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results")

        results = self.search(query=keywords, region=region, safesearch=safesearch)
        if results and max_results:
            results = results[:max_results]
        return results or []
