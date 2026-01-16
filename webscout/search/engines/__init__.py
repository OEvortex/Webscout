"""Static imports for all search engine modules."""

from __future__ import annotations

from ..base import BaseSearchEngine
from .bing import BingBase, BingImagesSearch, BingNewsSearch, BingSuggestionsSearch, BingTextSearch
from .brave import (
    BraveBase,
    BraveImages,
    BraveNews,
    BraveSuggestions,
    BraveTextSearch,
    BraveVideos,
)
from .duckduckgo import (
    DuckDuckGoAnswers,
    DuckDuckGoBase,
    DuckDuckGoImages,
    DuckDuckGoMaps,
    DuckDuckGoNews,
    DuckDuckGoSuggestions,
    DuckDuckGoTextSearch,
    DuckDuckGoTranslate,
    DuckDuckGoVideos,
    DuckDuckGoWeather,
)
from .mojeek import Mojeek
from .wikipedia import Wikipedia
from .yahoo import (
    YahooImages,
    YahooNews,
    YahooSearchEngine,
    YahooSuggestions,
    YahooText,
    YahooVideos,
)
from .yandex import Yandex
from .yep import YepBase, YepImages, YepSuggestions, YepTextSearch

# Engine categories mapping
ENGINES = {
    "text": {
        "brave": BraveTextSearch,
        "mojeek": Mojeek,
        "yandex": Yandex,
        "bing": BingTextSearch,
        "duckduckgo": DuckDuckGoTextSearch,
        "yep": YepTextSearch,
        "yahoo": YahooText,
    },
    "images": {
        "bing": BingImagesSearch,
        "brave": BraveImages,
        "duckduckgo": DuckDuckGoImages,
        "yep": YepImages,
        "yahoo": YahooImages,
    },
    "videos": {
        "brave": BraveVideos,
        "duckduckgo": DuckDuckGoVideos,
        "yahoo": YahooVideos,
    },
    "news": {
        "brave": BraveNews,
        "bing": BingNewsSearch,
        "duckduckgo": DuckDuckGoNews,
        "yahoo": YahooNews,
    },
    "suggestions": {
        "brave": BraveSuggestions,
        "bing": BingSuggestionsSearch,
        "duckduckgo": DuckDuckGoSuggestions,
        "yep": YepSuggestions,
        "yahoo": YahooSuggestions,
    },
    "answers": {
        "duckduckgo": DuckDuckGoAnswers,
    },
    "maps": {
        "duckduckgo": DuckDuckGoMaps,
    },
    "translate": {
        "duckduckgo": DuckDuckGoTranslate,
    },
    "weather": {
        "duckduckgo": DuckDuckGoWeather,
    },
}

__all__ = [
    "BraveBase",
    "BraveTextSearch",
    "BraveImages",
    "BraveVideos",
    "BraveNews",
    "BraveSuggestions",
    "Mojeek",
    "Wikipedia",
    "Yandex",
    "BingBase",
    "BingTextSearch",
    "BingImagesSearch",
    "BingNewsSearch",
    "BingSuggestionsSearch",
    "DuckDuckGoBase",
    "DuckDuckGoTextSearch",
    "DuckDuckGoImages",
    "DuckDuckGoVideos",
    "DuckDuckGoNews",
    "DuckDuckGoAnswers",
    "DuckDuckGoSuggestions",
    "DuckDuckGoMaps",
    "DuckDuckGoTranslate",
    "DuckDuckGoWeather",
    "YepBase",
    "YepTextSearch",
    "YepImages",
    "YepSuggestions",
    "YahooSearchEngine",
    "YahooText",
    "YahooImages",
    "YahooVideos",
    "YahooNews",
    "YahooSuggestions",
    "BaseSearchEngine",
    "ENGINES",
]
