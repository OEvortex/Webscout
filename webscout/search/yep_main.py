"""Yep unified search interface."""

from __future__ import annotations

from typing import List, Optional

from .base import BaseSearch
from .engines.yep.images import YepImages
from .engines.yep.suggestions import YepSuggestions
from .engines.yep.text import YepSearch as YepTextSearch
from .results import ImagesResult, TextResult


class YepSearch(BaseSearch):
    """Unified Yep search interface."""

    def text(
        self,
        keywords: str,
        region: str = "all",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[TextResult]:
        search = YepTextSearch()
        return search.run(keywords, region, safesearch, max_results)

    def images(
        self,
        keywords: str,
        region: str = "all",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[ImagesResult]:
        search = YepImages()
        return search.run(keywords, region, safesearch, max_results)

    def suggestions(self, keywords: str, region: str = "all") -> List[dict]:
        search = YepSuggestions()
        results = search.run(keywords, region)
        return [{"suggestion": s} for s in results]

    def videos(self, *args, **kwargs) -> List:
        raise NotImplementedError("Yep does not support video search")

    def news(self, *args, **kwargs) -> List:
        raise NotImplementedError("Yep does not support news search")

    def answers(self, *args, **kwargs) -> List:
        raise NotImplementedError("Yep does not support instant answers")

    def maps(self, *args, **kwargs) -> List:
        raise NotImplementedError("Yep does not support maps search")

    def translate(self, *args, **kwargs) -> List:
        raise NotImplementedError("Yep does not support translation")
