"""Brave videos search implementation.

This module provides a Brave video search engine that parses HTML responses
from Brave Search to extract video results from YouTube and other video platforms.

Example:
    >>> from webscout.search.engines.brave.videos import BraveVideos
    >>> searcher = BraveVideos()
    >>> results = searcher.run("python tutorial", max_results=10)
    >>> for video in results:
    ...     print(f"{video.title} - {video.url}")
"""

from __future__ import annotations

from time import sleep
from typing import Any

from webscout.scout import Scout

from ....search.results import VideosResult
from .base import BraveBase


class BraveVideos(BraveBase):
    """Brave videos search engine.

    Searches Brave Video Search and parses HTML responses to extract
    video results including title, URL, thumbnail, duration, channel,
    description, publish date, and view count.

    Attributes:
        name: Engine identifier name.
        provider: Provider identifier.
        category: Search category type.
        search_url: Base URL for video search.
    """

    name = "brave_videos"
    provider = "brave"
    category = "videos"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize Brave videos search client.

        Args:
            *args: Positional arguments passed to BraveBase.
            **kwargs: Keyword arguments passed to BraveBase.
        """
        super().__init__(*args, **kwargs)
        self.search_url = f"{self.base_url}/videos"

    def run(self, *args: Any, **kwargs: Any) -> list[VideosResult]:
        """Run video search on Brave.

        Args:
            *args: Positional arguments. First arg is the search query.
            **kwargs: Keyword arguments including:
                - keywords: Search query string.
                - region: Region code (e.g., 'us-en').
                - safesearch: Safe search level ('on', 'moderate', 'off').
                - max_results: Maximum number of results to return.
                - timelimit: Time filter for results.

        Returns:
            List of VideosResult objects containing video information.

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

        fetched_results: list[VideosResult] = []
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
        """Fetch HTML page from Brave videos search.

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

    def _parse_results_from_html(self, html: str) -> list[VideosResult]:
        """Parse HTML and extract video search results.

        Args:
            html: Raw HTML content from Brave videos search.

        Returns:
            List of VideosResult objects parsed from the HTML.
        """
        soup = Scout(html)
        results: list[VideosResult] = []

        # Video results are in div.video-snippet containers
        containers = soup.select("div.video-snippet")

        for container in containers:
            try:
                result = self._parse_video_container(container)
                if result and result.url:
                    results.append(result)
            except Exception:
                # Skip malformed results
                continue

        return results

    def _parse_video_container(self, container: Any) -> VideosResult | None:
        """Parse a single video container element.

        Args:
            container: Scout element representing a video result container.

        Returns:
            VideosResult object or None if parsing fails.
        """
        # Get video URL from main link
        url = ""
        link_elem = container.select_one("a[href]")
        if link_elem:
            url = link_elem.get("href", "").strip()

        if not url:
            return None

        # Get thumbnail
        thumbnail = ""
        thumb_elem = container.select_one("img.thumb, img.video-thumb")
        if thumb_elem:
            thumbnail = thumb_elem.get("src", "").strip()

        # Get duration
        duration = ""
        duration_elem = container.select_one(".over-thumbnail-info.duration")
        if duration_elem:
            duration = duration_elem.get_text(strip=True)

        # Get title from the result header
        title = ""
        title_elem = container.select_one(".snippet-title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Get channel/uploader
        uploader = ""
        channel_elem = container.select_one(".attr.channel")
        if channel_elem:
            uploader = channel_elem.get_text(strip=True)

        # Get provider (e.g., YouTube)
        provider = ""
        netloc_elem = container.select_one(".netloc.attr")
        if netloc_elem:
            provider = netloc_elem.get_text(strip=True)

        # Get description
        description = ""
        desc_elem = container.select_one(".snippet-description, p.desc")
        if desc_elem:
            description = desc_elem.get_text(strip=True)

        # Get publish date
        published = ""
        metrics_elem = container.select_one(".metrics")
        if metrics_elem:
            date_elem = metrics_elem.select_one(".attr:first-child")
            if date_elem:
                published = date_elem.get_text(strip=True)

        # Get view count from metrics
        view_count = 0
        if metrics_elem:
            view_elems = metrics_elem.select(".attr")
            for elem in view_elems:
                text = elem.get_text(strip=True)
                # Look for view count patterns (e.g., "1.31M", "34.1M", "17K")
                if any(c.isdigit() for c in text) and not any(
                    month in text.lower()
                    for month in [
                        "jan", "feb", "mar", "apr", "may", "jun",
                        "jul", "aug", "sep", "oct", "nov", "dec",
                        "hour", "day", "week", "month", "year", "ago",
                    ]
                ):
                    view_count = self._parse_view_count(text)
                    break

        return VideosResult(
            title=title,
            url=url,
            thumbnail=thumbnail,
            duration=duration,
            uploader=uploader,
            publisher=uploader,
            provider=provider,
            description=description,
            published=published,
            statistics={"views": view_count} if view_count else {},
            content=description,
            images={"thumbnail": thumbnail} if thumbnail else {},
        )

    def _parse_view_count(self, text: str) -> int:
        """Parse view count from text like '1.31M' or '17K'.

        Args:
            text: View count string with potential suffixes.

        Returns:
            Integer view count, or 0 if parsing fails.
        """
        try:
            text = text.strip().upper()
            multiplier = 1

            if text.endswith("K"):
                multiplier = 1000
                text = text[:-1]
            elif text.endswith("M"):
                multiplier = 1_000_000
                text = text[:-1]
            elif text.endswith("B"):
                multiplier = 1_000_000_000
                text = text[:-1]

            return int(float(text) * multiplier)
        except (ValueError, TypeError):
            return 0

    def extract_results(self, html_text: str) -> list[VideosResult]:
        """Extract video results from HTML text.

        This is an alias for _parse_results_from_html for API consistency.

        Args:
            html_text: Raw HTML content from Brave videos search.

        Returns:
            List of VideosResult objects parsed from the HTML.
        """
        return self._parse_results_from_html(html_text)


if __name__ == "__main__":
    # Test the BraveVideos search
    print("Testing BraveVideos search...")

    searcher = BraveVideos(timeout=15)

    try:
        # Test basic search
        results = searcher.run("python programming tutorial", max_results=5)

        print(f"\nFound {len(results)} video results:\n")
        for i, video in enumerate(results, 1):
            print(f"{i}. {video.title}")
            print(f"   URL: {video.url}")
            print(f"   Duration: {video.duration}")
            print(f"   Channel: {video.uploader}")
            print(f"   Provider: {video.provider}")
            print(f"   Published: {video.published}")
            if video.statistics:
                print(f"   Views: {video.statistics.get('views', 'N/A')}")
            print(f"   Thumbnail: {video.thumbnail[:80]}..." if video.thumbnail else "")
            print()

    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
