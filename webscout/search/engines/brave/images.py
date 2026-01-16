"""Brave images search implementation."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from ...base import BaseSearchEngine
from ...results import ImagesResult


class BraveImages(BaseSearchEngine[ImagesResult]):
    """Brave images search engine."""

    name = "brave_images"
    category = "images"
    provider = "brave"

    search_url = "https://search.brave.com/images"
    search_method = "GET"

    items_xpath = "//button[@class='image-result svelte-1qhxjcj']"
    elements_xpath: Mapping[str, str] = {
        "title": ".//img/@alt",
        "image": ".//img/@src",
        "source": ".//div[contains(@class, 'image-metadata-site')]//text()",
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
            query: Search query string.
            region: Region code (e.g., 'us-en').
            safesearch: Safe search level ('on', 'moderate', or 'off').
            timelimit: Time limit filter (optional).
            page: Page number for pagination.
            **kwargs: Additional arguments.

        Returns:
            Dictionary with query parameters for the request.
        """
        safesearch_map = {"on": "strict", "moderate": "moderate", "off": "off"}
        payload = {
            "q": query,
            "source": "web",
            "safesearch": safesearch_map.get(safesearch.lower(), "moderate"),
        }
        if timelimit:
            payload["tf"] = timelimit
        if page > 1:
            # Brave uses offset-based pagination with 40 results per page for images
            payload["offset"] = str((page - 1) * 40)
        return payload

    def extract_results(self, html_text: str) -> list[ImagesResult]:
        """Extract image results from HTML.

        Args:
            html_text: The HTML content to parse.

        Returns:
            List of ImagesResult objects extracted from the HTML.
        """
        if not self.parser:
            raise ImportError("lxml is required for result extraction")

        html_text = self.pre_process_html(html_text)
        tree = self.extract_tree(html_text)

        results = []
        items = tree.xpath(self.items_xpath) if self.items_xpath else []

        for item in items:
            result = ImagesResult()

            # Extract image URL (proxy URL)
            img_elements = item.xpath(".//img/@src")
            if img_elements:
                result.image = img_elements[0]

            # Extract alt text as title
            alt_elements = item.xpath(".//img/@alt")
            if alt_elements:
                result.title = alt_elements[0]

            # Extract source domain and title from metadata
            text_content = item.xpath(".//div[contains(@class, 'image-metadata')]//text()")
            if text_content:
                full_text = "".join(text_content).strip()
                # The text format is typically: "domain.com Title"
                parts = full_text.split("\n")
                if parts:
                    # First part is usually domain
                    result.source = parts[0].strip() if parts[0] else ""
                    # Try to improve title from metadata
                    if len(parts) > 1:
                        metadata_title = parts[1].strip()
                        if metadata_title and not result.title:
                            result.title = metadata_title

            # Extract dimensions if available in style attribute
            style = item.xpath("./@style")
            if style:
                style_str = style[0]
                # Parse CSS custom properties for dimensions
                # Format: --width: 500; --height: 889;
                if "--width:" in style_str:
                    try:
                        width_str = style_str.split("--width:")[1].split(";")[0].strip()
                        result.width = int(width_str)
                    except (ValueError, IndexError):
                        pass
                if "--height:" in style_str:
                    try:
                        height_str = (
                            style_str.split("--height:")[1].split(";")[0].strip()
                        )
                        result.height = int(height_str)
                    except (ValueError, IndexError):
                        pass

            # Try to extract original URL from the proxy URL
            # Brave proxy format: imgs.search.brave.com/[hash]/rs:fit:500:0:1:0/g:ce/[base64_url]
            if result.image:
                try:
                    result.url = self._extract_original_url(result.image)
                except Exception:
                    # If extraction fails, use the proxy URL
                    result.url = result.image

            results.append(result)

        return results

    def _extract_original_url(self, proxy_url: str) -> str:
        """Extract the original image URL from the Brave proxy URL.

        Args:
            proxy_url: The Brave proxy URL.

        Returns:
            The original image URL if successfully decoded, otherwise the proxy URL.
        """
        try:
            # Extract the base64-encoded part from the proxy URL
            # Format: https://imgs.search.brave.com/[hash]/rs:fit:500:0:1:0/g:ce/[base64_url]
            parts = proxy_url.split("/")
            if len(parts) > 0:
                # The base64 part is typically after g:ce/
                base64_part = parts[-1] if parts[-1] else ""
                if base64_part and len(base64_part) > 10:
                    # Base64 might have slashes replaced with URL-safe characters
                    # Restore them for decoding
                    normalized = (
                        base64_part.replace("-", "+")
                        .replace("_", "/")
                        .replace(" ", "")
                    )
                    # Add padding if necessary
                    padding = 4 - (len(normalized) % 4)
                    if padding and padding != 4:
                        normalized += "=" * padding

                    decoded = base64.b64decode(normalized).decode("utf-8", errors="ignore")
                    if decoded.startswith("http"):
                        return decoded
        except Exception:
            pass

        return proxy_url

    def run(self, *args, **kwargs) -> list[ImagesResult]:
        """Run image search on Brave.

        Args:
            keywords: Search query.
            region: Region code.
            safesearch: Safe search level.
            max_results: Maximum number of results (optional).
            **kwargs: Additional arguments.

        Returns:
            List of ImagesResult objects.
        """
        keywords = args[0] if args else kwargs.get("keywords")
        if keywords is None:
            keywords = ""
        region = args[1] if len(args) > 1 else kwargs.get("region", "us-en")
        safesearch = (
            args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        )
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results")

        results = self.search(
            query=keywords, region=region, safesearch=safesearch
        )
        if results and max_results:
            results = results[:max_results]
        return results or []
