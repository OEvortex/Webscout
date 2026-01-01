"""Wikipedia text search engine."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from ...utils import json_loads
from ..base import BaseSearchEngine
from ..results import TextResult


class Wikipedia(BaseSearchEngine[TextResult]):
    """Wikipedia text search engine."""

    name = "wikipedia"
    category = "text"
    provider = "wikipedia"
    priority = 2

    search_url = "https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={query}"
    search_method = "GET"

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        _country, lang = region.lower().split("-")
        encoded_query = quote(query)
        self.search_url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&profile=fuzzy&limit=1&search={encoded_query}"
        )
        payload: dict[str, Any] = {}
        self.lang = lang  # used in extract_results
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text."""
        json_data = json_loads(html_text)
        if not json_data or len(json_data) < 4:
            return []

        results = []
        titles, descriptions, urls = json_data[1], json_data[2], json_data[3]

        for title, description, url in zip(titles, descriptions, urls):
            result = TextResult()
            result.title = title
            result.body = description
            result.href = url
            results.append(result)

        return results

    def run(self, *args, **kwargs) -> list[TextResult]:
        """Run text search on Wikipedia.

        Args:
            keywords: Search query.
            region: Region code.
            safesearch: Safe search level (ignored).
            max_results: Maximum number of results.

        Returns:
            List of TextResult objects.
        """
        keywords = args[0] if args else kwargs.get("keywords")
        if keywords is None:
            keywords = ""
        region = args[1] if len(args) > 1 else kwargs.get("region", "en-us")
        safesearch = args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results")

        results = self.search(query=keywords, region=region, safesearch=safesearch)
        if results and max_results:
            results = results[:max_results]
        return results or []
