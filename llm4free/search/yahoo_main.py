"""Yahoo unified search interface."""

from __future__ import annotations

from typing import List, Optional

from .base import BaseSearch
from .engines.yahoo.answers import YahooAnswers
from .engines.yahoo.images import YahooImages
from .engines.yahoo.maps import YahooMaps
from .engines.yahoo.news import YahooNews
from .engines.yahoo.suggestions import YahooSuggestions
from .engines.yahoo.text import YahooText
from .engines.yahoo.translate import YahooTranslate
from .engines.yahoo.videos import YahooVideos
from .engines.yahoo.weather import YahooWeather
from .results import ImagesResult, NewsResult, TextResult, VideosResult


class YahooSearch(BaseSearch):
    """Unified Yahoo search interface."""

    def text(
        self,
        keywords: str,
        region: str = "us",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[TextResult]:
        search = YahooText()
        return search.run(
            keywords=keywords, region=region, safesearch=safesearch, max_results=max_results
        )

    def images(
        self,
        keywords: str,
        region: str = "us",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[ImagesResult]:
        search = YahooImages()
        return search.run(
            keywords=keywords, region=region, safesearch=safesearch, max_results=max_results
        )

    def videos(
        self,
        keywords: str,
        region: str = "us",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[VideosResult]:
        search = YahooVideos()
        return search.run(
            keywords=keywords, region=region, safesearch=safesearch, max_results=max_results
        )

    def news(
        self,
        keywords: str,
        region: str = "us",
        safesearch: str = "moderate",
        max_results: Optional[int] = None,
    ) -> List[NewsResult]:
        search = YahooNews()
        return search.run(
            keywords=keywords, region=region, safesearch=safesearch, max_results=max_results
        )

    def suggestions(self, keywords: str, region: str = "us") -> List[dict]:
        search = YahooSuggestions()
        results = search.run(keywords, region)
        return [{"suggestion": s} for s in results]

    def answers(self, keywords: str) -> List[dict]:
        search = YahooAnswers()
        return search.run(keywords)

    def maps(
        self,
        keywords: str,
        place: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        county: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postalcode: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        radius: int = 0,
        max_results: Optional[int] = None,
    ) -> List[dict]:
        search = YahooMaps()
        return search.run(
            keywords,
            place,
            street,
            city,
            county,
            state,
            country,
            postalcode,
            latitude,
            longitude,
            radius,
            max_results,
        )

    def translate(
        self, keywords: str, from_lang: Optional[str] = None, to_lang: str = "en"
    ) -> List[dict]:
        search = YahooTranslate()
        return search.run(keywords, from_lang, to_lang)

    def weather(self, keywords: str) -> List[dict]:
        search = YahooWeather()
        return search.run(keywords)
