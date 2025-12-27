"""Mojeek search engine implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from ..base import BaseSearchEngine
from ..results import TextResult


class Mojeek(BaseSearchEngine[TextResult]):
    """Mojeek search engine."""

    name = "mojeek"
    category = "text"
    provider = "mojeek"

    search_url = "https://www.mojeek.com/search"
    search_method = "GET"

    items_xpath = "//ul[contains(@class, 'results')]/li"
    elements_xpath: Mapping[str, str] = {
        "title": ".//h2//text()",
        "href": ".//h2/a/@href",
        "body": ".//p[@class='s']//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        safesearch_base = {"on": "1", "moderate": "0", "off": "0"}
        payload = {"q": query, "safe": safesearch_base[safesearch.lower()]}
        if page > 1:
            payload["s"] = f"{(page - 1) * 10 + 1}"
        return payload

    def run(self, *args, **kwargs) -> list[TextResult]:
        """Run text search on Mojeek.

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
