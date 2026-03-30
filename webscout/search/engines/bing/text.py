"""Bing text search."""

from __future__ import annotations

from time import sleep
from typing import List, Optional

from webscout.scout import Scout
from webscout.search.results import TextResult

from .base import BingBase


class BingTextSearch(BingBase):
    name = "bing"
    category = "text"

    def _extract_from_html(self, html: str, max_results: int) -> List[TextResult]:
        """Extract results from Bing HTML using multiple selector strategies."""
        results: List[TextResult] = []
        soup = Scout(html)

        # Strategy 1: Standard Bing result selectors
        selectors = [
            ("ol#b_results > li.b_algo", "h2", "h2 a", "p"),
            ("li.b_algo", "h2", "h2 a", "p"),
            ("#b_results .b_algo", "h2", "h2 a", ".b_caption p"),
            (".b_algo", ".b_title h2", ".b_title a", ".b_caption p"),
            ("#b_results li", "h2", "h2 a", "p"),
        ]

        for sel_container, sel_title, sel_link, sel_body in selectors:
            items = soup.select(sel_container)
            if items:
                for item in items:
                    if len(results) >= max_results:
                        break
                    title_tag = item.select_one(sel_title)
                    link_tag = item.select_one(sel_link)
                    body_tag = item.select_one(sel_body)

                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        href = link_tag.get("href", "")
                        body = body_tag.get_text(strip=True) if body_tag else ""

                        if title and href:
                            # Decode Bing redirect URLs
                            href = self._decode_bing_url(href)
                            results.append(TextResult(title=title, href=href, body=body))
                if results:
                    return results[:max_results]

        # Strategy 2: Regex fallback for obfuscated pages
        import re

        # Look for structured result patterns in script tags
        script_data = re.findall(r'"Title"\s*:\s*"([^"]+)".*?"Url"\s*:\s*"([^"]+)"', html[:100000])
        for title, url in script_data[:max_results]:
            if url.startswith("http"):
                results.append(TextResult(title=title, href=self._decode_bing_url(url), body=""))
        if results:
            return results[:max_results]

        # Strategy 3: Find any <a> with <h2> parent or nearby
        links = re.findall(
            r'<h2[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html[:100000], re.DOTALL
        )
        for href, text in links[:max_results]:
            clean_text = re.sub(r"<[^>]+>", "", text).strip()
            if clean_text:
                results.append(
                    TextResult(title=clean_text, href=self._decode_bing_url(href), body="")
                )

        return results[:max_results]

    def _decode_bing_url(self, href: str) -> str:
        """Decode Bing's encoded redirect URLs."""
        if "/ck/a" in href or "/cr?" in href:
            from urllib.parse import parse_qs, unquote, urlparse

            try:
                parsed = urlparse(href)
                query_params = parse_qs(parsed.query)
                if "u" in query_params:
                    encoded_url = query_params["u"][0]
                    if encoded_url.startswith("a1"):
                        encoded_url = encoded_url[2:]
                    padding = len(encoded_url) % 4
                    if padding:
                        encoded_url += "=" * (4 - padding)
                    import base64

                    decoded = base64.urlsafe_b64decode(encoded_url).decode()
                    return decoded
                # Try rurl parameter
                if "rurl" in query_params:
                    return unquote(query_params["rurl"][0])
            except Exception:
                pass
        return href

    def run(self, *args, **kwargs) -> List[TextResult]:
        keywords = args[0] if args else kwargs.get("keywords")
        args[1] if len(args) > 1 else kwargs.get("region", "us")
        args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results", 10)
        unique = kwargs.get("unique", True)

        if max_results is None:
            max_results = 10

        if not keywords:
            raise ValueError("Keywords are mandatory")

        fetched_results: List[TextResult] = []
        fetched_links = set()

        def fetch_page(url: str) -> str | None:
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception:
                return None

        # Try standard Bing search first, then mobile fallback
        urls_to_try = [
            f"{self.base_url}/search?q={keywords}&form=QBLH",
            f"https://m.bing.com/search?q={keywords}",
        ]

        for base_url in urls_to_try:
            html = fetch_page(base_url)
            if not html:
                continue

            page_results = self._extract_from_html(html, max_results)

            for r in page_results:
                if len(fetched_results) >= max_results:
                    break
                if unique and r.href in fetched_links:
                    continue
                fetched_links.add(r.href)
                fetched_results.append(r)

            if fetched_results:
                break

        return fetched_results[:max_results]
