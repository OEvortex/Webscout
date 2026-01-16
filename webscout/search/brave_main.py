"""Brave unified search interface."""

from __future__ import annotations

from typing import Dict, List, Optional

from .base import BaseSearch
from .engines.brave.images import BraveImages
from .engines.brave.news import BraveNews
from .engines.brave.suggestions import BraveSuggestions
from .engines.brave.text import BraveTextSearch
from .engines.brave.videos import BraveVideos
from .results import ImagesResult, NewsResult, TextResult, VideosResult


class BraveSearch(BaseSearch):
    """Unified Brave search interface."""

    def text(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[TextResult]:
        search = BraveTextSearch()
        return search.run(keywords, region, safesearch, max_results)

    def images(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[ImagesResult]:
        """Search Brave Images."""
        search = BraveImages()
        return search.run(keywords, region, safesearch, max_results)

    def news(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[NewsResult]:
        """Search Brave News."""
        search = BraveNews()
        return search.run(keywords, region, safesearch, max_results)

    def suggestions(
        self,
        query: str,
        rich: bool = True,
        country: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Search Brave suggestions/autocomplete."""
        search = BraveSuggestions()
        results = search.run(query, rich=rich, country=country, max_results=max_results)
        return [
            {
                "query": s.query,
                "is_entity": str(s.is_entity),
                "name": s.name,
                "desc": s.desc,
            }
            for s in results
        ]

    def answers(self, *args, **kwargs) -> List[Dict[str, str]]:
        """Instant answers not yet implemented for Brave."""
        raise NotImplementedError("Brave instant answers not yet implemented")

    def maps(self, *args, **kwargs) -> List[Dict[str, str]]:
        """Maps search not yet implemented for Brave."""
        raise NotImplementedError("Brave maps search not yet implemented")

    def translate(self, *args, **kwargs) -> List[Dict[str, str]]:
        """Translation not yet implemented for Brave."""
        raise NotImplementedError("Brave translation not yet implemented")

    def videos(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[VideosResult]:
        """Search Brave Videos."""
        search = BraveVideos()
        return search.run(keywords, region, safesearch, max_results)
