"""Dogpile search engine implementation.

Dogpile is a metasearch engine that fetches results from multiple search engines
including Google, Yahoo, Bing, and others.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Dogpile(BaseSearchEngine[TextResult]):
    """Dogpile search engine.

    A metasearch engine that aggregates results from multiple search engines.

    Attributes:
        name: Engine identifier
        category: Search category (text)
        provider: Result provider name
        search_url: Base URL for searches
        search_method: HTTP method (GET)
        items_xpath: XPath to locate result items
        elements_xpath: XPath mappings for extracting result fields
    """

    name = "dogpile"
    category = "text"
    provider = "dogpile"

    search_url = "https://www.dogpile.com/serp"
    search_method = "GET"

    # XPath selectors for result extraction
    # Dogpile results structure:
    # <div class="web-google__result">
    #   <a class="web-google__title" href="...">Title</a>
    #   <span class="web-google__url">url</span>
    #   <span class="web-google__description">Description text</span>
    # </div>
    items_xpath = "//div[contains(@class, 'web-') and contains(@class, '__result')]"

    elements_xpath: Mapping[str, str] = {
        "title": ".//a[contains(@class, '__title')]//text()",
        "href": ".//a[contains(@class, '__title')]/@href",
        "body": ".//span[contains(@class, '__description')]//text()",
    }

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build a payload for the search request.

        Args:
            query: Search query string
            region: Region code (not used by Dogpile)
            safesearch: Safe search level (not used by Dogpile)
            timelimit: Time limit filter (not used by Dogpile)
            page: Page number for pagination
            **kwargs: Additional parameters

        Returns:
            Dictionary with query parameters
        """
        payload: dict[str, Any] = {"q": query}

        sc = kwargs.get("sc")
        if isinstance(sc, str) and sc:
            payload["sc"] = sc

        # Dogpile uses 'page' parameter for pagination
        if page > 1:
            payload["page"] = page

        return payload

    def pre_process_html(self, html_text: str) -> str:
        """Pre-process HTML before extraction.

        Args:
            html_text: Raw HTML content

        Returns:
            Processed HTML content
        """
        # Dogpile may use URL encoding in result links
        return html_text

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process extracted results.

        Args:
            results: List of extracted TextResult objects

        Returns:
            Processed list of TextResult objects
        """
        # Clean up and filter results
        cleaned_results = []
        for result in results:
            # Ensure we have valid URLs
            if result.href and result.href.startswith("http"):
                # Clean up title and body
                result.title = result.title.strip()
                result.body = result.body.strip()
                cleaned_results.append(result)
        return cleaned_results

    def run(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: int | None = None,
        pages: int = 1,
        **kwargs: Any,
    ) -> list[TextResult]:
        """Run text search on Dogpile.

        Args:
            keywords: Search query string
            region: Region code (not used by Dogpile)
            safesearch: Safe search level (not used by Dogpile)
            max_results: Maximum number of results to return
            pages: Number of pages to search
            **kwargs: Additional parameters

        Returns:
            List of TextResult objects
        """
        all_results: list[TextResult] = []

        for page in range(1, pages + 1):
            results = self.search(
                query=keywords,
                region=region,
                safesearch=safesearch,
                page=page,
                **kwargs,
            )
            if results:
                all_results.extend(results)
            else:
                break

        if max_results and all_results:
            all_results = all_results[:max_results]

        return all_results
