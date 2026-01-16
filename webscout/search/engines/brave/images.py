"""Brave images search implementation."""

from __future__ import annotations

import base64
from typing import Any, Mapping

from webscout.scout import Scout

from ....search.results import ImagesResult
from .base import BraveBase


class BraveImages(BraveBase):
    """Brave images search engine."""

    name = "brave_images"
    provider = "brave"
    category = "images"
    search_method = "GET"
    items_xpath = "//button[contains(@class, 'image-result')]"
    elements_xpath: Mapping[str, str] = {
        "title": ".//img/@alt",
        "image": ".//img/@src",
        "source": "string(.//div[contains(@class, 'metadata')])",
    }
    result_type = ImagesResult

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.search_url = f"{self.base_url}/images"

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **_: Any,
    ) -> dict[str, str]:
        """Build query parameters for Brave image search."""

        safesearch_map = {"on": "strict", "moderate": "moderate", "off": "off"}
        payload: dict[str, str] = {
            "q": query,
            "source": "web",
            "safesearch": safesearch_map.get(safesearch.lower(), "moderate"),
            "page": str(page),
        }

        # Brave uses "offset" in multiples of 40 (page 1 => 0)
        if page > 1:
            payload["offset"] = str((page - 1) * 40)

        if timelimit:
            payload["tf"] = timelimit

        if region:
            payload["region"] = region

        return payload

    def run(self, *args: Any, **kwargs: Any) -> list[ImagesResult]:
        """Run image search on Brave."""

        keywords = args[0] if args else kwargs.get("keywords")
        region = args[1] if len(args) > 1 else kwargs.get("region", "us-en")
        safesearch = args[2] if len(args) > 2 else kwargs.get("safesearch", "moderate")
        max_results = args[3] if len(args) > 3 else kwargs.get("max_results", 10)

        if max_results is None:
            max_results = 10

        if not keywords:
            raise ValueError("Keywords are mandatory")

        safesearch_value = self.build_payload(keywords, region, safesearch, None)["safesearch"]

        fetched_results: list[ImagesResult] = []
        fetched_urls: set[str] = set()

        def fetch_page(url: str) -> str:
            """Fetch page content."""
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # pragma: no cover - network handling
                raise Exception(f"Failed to fetch page: {str(exc)}") from exc

        page = 1
        while len(fetched_results) < max_results:
            params = {
                "q": keywords,
                "page": str(page),
                "safesearch": safesearch_value,
            }
            full_url = f"{self.search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            html = fetch_page(full_url)
            soup = Scout(html)

            img_containers = soup.select("button.image-result")
            if not img_containers:
                break

            for container in img_containers:
                if len(fetched_results) >= max_results:
                    break

                img_elem = container.select_one("img")
                if not img_elem:
                    continue

                title = img_elem.get("alt", "")
                image_url = img_elem.get("src", "")

                source_elem = container.select_one('div[class*="metadata"]')
                source = source_elem.get_text(strip=True) if source_elem else ""

                width = 0
                height = 0
                style = container.get("style", "")
                if style:
                    if "--width:" in style:
                        try:
                            width = int(style.split("--width:")[1].split(";")[0].strip())
                        except (ValueError, IndexError):
                            pass
                    if "--height:" in style:
                        try:
                            height = int(style.split("--height:")[1].split(";")[0].strip())
                        except (ValueError, IndexError):
                            pass

                original_url = image_url
                if image_url and "imgs.search.brave.com" in image_url:
                    try:
                        original_url = self._extract_original_url(image_url)
                    except Exception:
                        original_url = image_url

                if image_url and image_url not in fetched_urls:
                    fetched_urls.add(image_url)
                    fetched_results.append(
                        ImagesResult(
                            title=title,
                            image=image_url,
                            thumbnail=image_url,
                            url=original_url,
                            height=height,
                            width=width,
                            source=source,
                        )
                    )

            page += 1

            if self.sleep_interval:
                from time import sleep

                sleep(self.sleep_interval)

        return fetched_results[:max_results]

    def extract_results(self, html_text: str) -> list[ImagesResult]:
        """Parse Brave image search HTML into results."""

        soup = Scout(html_text)
        results: list[ImagesResult] = []
        for container in soup.select("button.image-result"):
            img_elem = container.select_one("img")
            if not img_elem:
                continue

            title = img_elem.get("alt", "")
            image_url = img_elem.get("src", "")
            source_elem = container.select_one('div[class*="metadata"]')
            source = source_elem.get_text(strip=True) if source_elem else ""

            results.append(
                ImagesResult(
                    title=title,
                    image=image_url,
                    thumbnail=image_url,
                    url=image_url,
                    height=0,
                    width=0,
                    source=source,
                )
            )

        return results

    def _extract_original_url(self, proxy_url: str) -> str:
        """Extract the original image URL from the Brave proxy URL."""

        try:
            parts = proxy_url.split("/")
            base64_part = parts[-1] if parts else ""
            if base64_part and len(base64_part) > 10:
                normalized = base64_part.replace("-", "+").replace("_", "/").replace(" ", "")
                padding = 4 - (len(normalized) % 4)
                if padding and padding != 4:
                    normalized += "=" * padding

                decoded = base64.b64decode(normalized).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
        except Exception:
            pass

        return proxy_url
