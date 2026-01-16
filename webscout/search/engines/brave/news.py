"""Brave news search implementation.

This module provides a Brave news search engine that parses HTML responses
from Brave Search to extract news article results.

Example:
    >>> from webscout.search.engines.brave.news import BraveNews
    >>> searcher = BraveNews()
    >>> results = searcher.run("technology news", max_results=10)
    >>> for article in results:
    ...     print(f"{article.title} - {article.source}")
"""

from __future__ import annotations

from time import sleep
from typing import Any

from webscout.scout import Scout

from ....search.results import NewsResult
from .base import BraveBase


class BraveNews(BraveBase):
    """Brave news search engine.

    Searches Brave News Search and parses HTML responses to extract
    news article results including title, URL, source, date, description,
    and thumbnail image.

    Attributes:
        name: Engine identifier name.
        provider: Provider identifier.
        category: Search category type.
        search_url: Base URL for news search.
    """

    name = "brave_news"
    provider = "brave"
    category = "news"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize Brave news search client.

        Args:
            *args: Positional arguments passed to BraveBase.
            **kwargs: Keyword arguments passed to BraveBase.
        """
        super().__init__(*args, **kwargs)
        self.search_url = f"{self.base_url}/news"

    def run(self, *args: Any, **kwargs: Any) -> list[NewsResult]:
        """Run news search on Brave.

        Args:
            *args: Positional arguments. First arg is the search query.
            **kwargs: Keyword arguments including:
                - keywords: Search query string.
                - region: Region code (e.g., 'us-en').
                - safesearch: Safe search level ('on', 'moderate', 'off').
                - max_results: Maximum number of results to return.
                - timelimit: Time filter for results ('d' for day, 'w' for week, etc.).

        Returns:
            List of NewsResult objects containing news article information.

        Raises:
            ValueError: If no keywords are provided.
            Exception: If the HTTP request fails.
        """
        keywords = args[0] if args else kwargs.get("keywords")
        region = args[1] if len(args) > 1 else kwargs.get("region", "us-en")
        safesearch = args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results", 10)
        timelimit = kwargs.get("timelimit")

        if max_results is None:
            max_results = 10

        if not keywords:
            raise ValueError("Keywords are mandatory")

        safesearch_map = {"on": "strict", "moderate": "moderate", "off": "off"}
        safesearch_str = str(safesearch).lower() if safesearch else "moderate"
        safesearch_value = safesearch_map.get(safesearch_str, "moderate")

        fetched_results: list[NewsResult] = []
        fetched_urls: set[str] = set()

        offset = 0
        while len(fetched_results) < max_results:
            params: dict[str, str] = {
                "q": keywords,
                "source": "web",
                "safesearch": safesearch_value,
                "spellcheck": "0",
            }

            if offset > 0:
                params["offset"] = str(offset)

            if timelimit:
                params["tf"] = timelimit

            if region:
                params["region"] = region

            html = self._fetch_page(params)
            page_results = self._parse_results_from_html(html)

            if not page_results:
                break

            for result in page_results:
                if len(fetched_results) >= max_results:
                    break
                if result.url and result.url not in fetched_urls:
                    fetched_urls.add(result.url)
                    fetched_results.append(result)

            offset += 1

            if self.sleep_interval:
                sleep(self.sleep_interval)

        return fetched_results[:max_results]

    def _fetch_page(self, params: dict[str, str]) -> str:
        """Fetch HTML page from Brave news search.

        Args:
            params: Query parameters for the request.

        Returns:
            HTML content of the response.

        Raises:
            Exception: If the request fails after retries.
        """
        headers = dict(self.session.headers) if getattr(self, "session", None) else {}
        headers.update({
            "Referer": "https://search.brave.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

        attempts = 3
        backoff = 1.0
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                resp = self.session.get(
                    self.search_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                last_exc = exc
                try:
                    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                except Exception:
                    code = None
                if code in (429, 500, 502, 503, 504):
                    sleep(backoff)
                    backoff *= 2
                    continue
                raise Exception(f"Failed to GET {self.search_url}: {exc}") from exc

        raise Exception(f"Failed to GET {self.search_url} after retries: {last_exc}") from last_exc

    def _parse_results_from_html(self, html: str) -> list[NewsResult]:
        """Parse HTML and extract news search results.

        Args:
            html: Raw HTML content from Brave news search.

        Returns:
            List of NewsResult objects parsed from the HTML.
        """
        soup = Scout(html)
        results: list[NewsResult] = []

        # News results are in div.snippet containers with data-type="news"
        containers = soup.select('div.snippet[data-type="news"]')

        # Fallback: try generic snippet containers in main
        if not containers:
            main = soup.select_one("main")
            if main:
                containers = main.select("div.snippet")

        for container in containers:
            try:
                result = self._parse_news_container(container)
                if result and result.url:
                    results.append(result)
            except Exception:
                # Skip malformed results
                continue

        return results

    def _parse_news_container(self, container: Any) -> NewsResult | None:
        """Parse a single news container element.

        Args:
            container: Scout element representing a news result container.

        Returns:
            NewsResult object or None if parsing fails.
        """
        # Get article URL from result header link
        url = ""
        link_elem = container.select_one("a.result-header")
        if link_elem:
            url = link_elem.get("href", "").strip()

        if not url:
            # Try alternate link location
            link_elem = container.select_one("a[href]")
            if link_elem:
                url = link_elem.get("href", "").strip()

        if not url:
            return None

        # Get title
        title = ""
        title_elem = container.select_one(".snippet-title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Get source (publisher)
        source = ""
        source_elem = container.select_one(".netloc")
        if source_elem:
            source = source_elem.get_text(strip=True)

        # Get publication date
        date = ""
        # Date is typically in a span.attr after the separator
        cite_elem = container.select_one("cite.snippet-url")
        if cite_elem:
            # Look for date patterns (e.g., "5 hours ago", "1 day ago", "January 15, 2026")
            attr_elems = cite_elem.select(".attr")
            for elem in attr_elems:
                text = elem.get_text(strip=True)
                # Skip separators
                if text == "•":
                    continue
                # Check if this looks like a date
                if self._is_date_text(text):
                    date = text
                    break

        # Get description
        body = ""
        desc_elem = container.select_one("p.desc, .snippet-description")
        if desc_elem:
            body = desc_elem.get_text(strip=True)

        # Get thumbnail image
        image = ""
        img_elem = container.select_one(".image-wrapper img, img")
        if img_elem:
            image = img_elem.get("src", "").strip()
            # Skip favicon images
            if "favicon" in image.lower() or "size-xs" in (img_elem.get("class") or ""):
                image = ""

        return NewsResult(
            title=title,
            url=url,
            source=source,
            date=date,
            body=body,
            image=image,
        )

    def _is_date_text(self, text: str) -> bool:
        """Check if text appears to be a date.

        Args:
            text: Text string to check.

        Returns:
            True if text looks like a date, False otherwise.
        """
        text_lower = text.lower()

        # Check for relative time patterns
        relative_patterns = [
            "hour", "hours", "minute", "minutes", "second", "seconds",
            "day", "days", "week", "weeks", "month", "months", "year", "years",
            "ago", "yesterday", "today",
        ]
        if any(pattern in text_lower for pattern in relative_patterns):
            return True

        # Check for month names
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        ]
        if any(month in text_lower for month in months):
            return True

        return False

    def extract_results(self, html_text: str) -> list[NewsResult]:
        """Extract news results from HTML text.

        This is an alias for _parse_results_from_html for API consistency.

        Args:
            html_text: Raw HTML content from Brave news search.

        Returns:
            List of NewsResult objects parsed from the HTML.
        """
        return self._parse_results_from_html(html_text)


if __name__ == "__main__":
    # Test the BraveNews search
    print("Testing BraveNews search...")

    searcher = BraveNews(timeout=15)

    try:
        # Test basic search
        results = searcher.run("technology", max_results=5)

        print(f"\nFound {len(results)} news results:\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   Source: {article.source}")
            print(f"   Date: {article.date}")
            print(f"   Description: {article.body[:100]}..." if article.body else "")
            print(f"   Image: {article.image[:80]}..." if article.image else "")
            print()

    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
