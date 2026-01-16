"""Brave text search."""

from __future__ import annotations

from time import sleep
from typing import List, Optional

from webscout.scout import Scout

from ....search.results import TextResult
from .base import BraveBase


class BraveTextSearch(BraveBase):
    """Brave text/web search."""

    name = "brave"
    category = "text"

    def run(self, *args, **kwargs) -> List[TextResult]:
        """Perform text search on Brave using offset pagination.

        Uses server-rendered HTML and parses result containers with CSS selectors.
        """
        from typing import cast

        keywords = args[0] if args else kwargs.get("keywords")
        if not keywords:
            raise ValueError("Keywords are mandatory")

        safesearch = args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results", 10)
        if max_results is None:
            max_results = 10

        safesearch_map = {"on": "strict", "moderate": "moderate", "off": "off"}
        safesearch_value = safesearch_map.get(safesearch.lower(), "moderate")

        start_offset = int(kwargs.get("start_offset", 0))
        offset = start_offset

        fetched_results: List[TextResult] = []
        fetched_hrefs: set[str] = set()

        def fetch_html(params: dict) -> str:
            url = f"{self.base_url}/search"
            # Merge session headers to include fingerprint (User-Agent, etc.)
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
                    resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                    resp.raise_for_status()
                    return resp.text
                except Exception as exc:  # network or HTTP errors
                    last_exc = exc
                    # If it's a 429 / transient server error, back off and retry
                    try:
                        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                    except Exception:
                        code = None
                    if code in (429, 500, 502, 503, 504):
                        sleep(backoff)
                        backoff *= 2
                        continue
                    # As a last attempt, try a simple GET without params appended (fallback)
                    try:
                        fallback_resp = self.session.get(url + "?" + "&".join(f"{k}={v}" for k, v in params.items()), headers=headers, timeout=self.timeout)
                        fallback_resp.raise_for_status()
                        return fallback_resp.text
                    except Exception:
                        # Final fallback: try using the requests library (less features but sometimes works)
                        try:
                            import requests

                            r = requests.get(url, params=params, headers=headers, timeout=self.timeout, verify=getattr(self, "verify", True))
                            r.raise_for_status()
                            return r.text
                        except Exception:
                            raise Exception(f"Failed to GET {url} with {params}: {exc}") from exc
            raise Exception(f"Failed to GET {url} after retries: {last_exc}") from last_exc

        # Pagination: offset param is a 0-based page index
        while len(fetched_results) < max_results:
            params = {"q": keywords, "source": "web", "offset": str(offset), "spellcheck": "0"}
            if safesearch_value:
                params["safesearch"] = safesearch_value

                html = fetch_html(params)
            # Parse and extract results using helper
            page_results = self._parse_results_from_html(html)

            if not page_results:
                break

            for res in page_results:
                if len(fetched_results) >= max_results:
                    break
                if res.href and res.href not in fetched_hrefs:
                    fetched_hrefs.add(res.href)
                    fetched_results.append(res)

            offset += 1
            if self.sleep_interval:
                sleep(self.sleep_interval)

        return fetched_results[:max_results]

    def _parse_results_from_html(self, html: str) -> List[TextResult]:
        """Parse HTML and extract text search results.

        This method is separated for testability.
        """
        soup = Scout(html)
        containers = soup.select("div.result-content")
        results: List[TextResult] = []

        for container in containers:
            a_elem = container.select_one("a[href]")
            # Title may be in .title.search-snippet-title or nested inside the anchor
            title_elem = container.select_one(".title.search-snippet-title") or (a_elem.select_one(".title") if a_elem else None)

            # Try multiple snippet locations: inside container, sibling .snippet, parent fallbacks
            body = ""
            candidates = []
            # inside container
            candidates.append(container.select_one(".generic-snippet"))
            candidates.append(container.select_one(".snippet .generic-snippet"))
            candidates.append(container.select_one(".description"))
            candidates.append(container.select_one(".result-snippet"))
            candidates.append(container.select_one("p"))

            # sibling .snippet
            try:
                fn = getattr(container, "find_next_sibling", None)
                if callable(fn):
                    sib = fn("div", class_="snippet")
                    if sib:
                        candidates.append(sib.select_one(".generic-snippet"))
            except Exception:
                pass

            # parent-level fallbacks
            if container.parent:
                candidates.append(container.parent.select_one(".snippet .generic-snippet"))
                candidates.append(container.parent.select_one(".generic-snippet"))

            for c in candidates:
                if c:
                    text = c.get_text(strip=True)
                    if text:
                        body = text
                        break

            if a_elem and title_elem:
                href = a_elem.get("href", "").strip()
                title = title_elem.get_text(strip=True)
                results.append(TextResult(title=title, href=href, body=body))

        return results
