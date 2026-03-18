"""Live tests for webscout search engines.

These tests exercise the real search providers against the network.
Run only the live suite with: uv run pytest tests/search/ -m live
"""
from __future__ import annotations

import pytest

from webscout.search import (
    BingSearch,
    BraveSearch,
    DuckDuckGoSearch,
    Mojeek,
    Wikipedia,
    YahooSearch,
    Yandex,
    YepSearch,
)

# Live tests require network access and are enabled through the ``live`` marker.
live_test = pytest.mark.live


class TestDuckDuckGo:
    """Tests for DuckDuckGo search engine."""

    @live_test
    def test_text_search(self):
        """Test DuckDuckGo text search."""
        ddg = DuckDuckGoSearch()
        results = ddg.text("python", max_results=2)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert hasattr(results[0], "title")
        assert hasattr(results[0], "href")

    @live_test
    def test_videos_search(self):
        """Test DuckDuckGo videos search."""
        ddg = DuckDuckGoSearch()
        results = ddg.videos("python tutorial", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_news_search(self):
        """Test DuckDuckGo news search."""
        ddg = DuckDuckGoSearch()
        results = ddg.news("python", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_suggestions(self):
        """Test DuckDuckGo suggestions."""
        ddg = DuckDuckGoSearch()
        results = ddg.suggestions("python")
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_answers(self):
        """Test DuckDuckGo instant answers."""
        ddg = DuckDuckGoSearch()
        results = ddg.answers("what is python")
        assert isinstance(results, list)

    @live_test
    def test_translate(self):
        """Test DuckDuckGo translation."""
        ddg = DuckDuckGoSearch()
        results = ddg.translate("hello", from_lang="en", to_lang="es")
        assert isinstance(results, list)


class TestBing:
    """Tests for Bing search engine."""

    @live_test
    def test_text_search(self):
        """Test Bing text search."""
        bing = BingSearch()
        results = bing.text("python", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_images_search(self):
        """Test Bing images search."""
        bing = BingSearch()
        results = bing.images("python logo", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_news_search(self):
        """Test Bing news search."""
        bing = BingSearch()
        results = bing.news("python", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_suggestions(self):
        """Test Bing suggestions."""
        bing = BingSearch()
        results = bing.suggestions("python")
        assert isinstance(results, list)


class TestBrave:
    """Tests for Brave search engine."""

    @live_test
    def test_text_search(self):
        """Test Brave text search."""
        brave = BraveSearch()
        results = brave.text("python", max_results=2)
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_images_search(self):
        """Test Brave images search."""
        brave = BraveSearch()
        results = brave.images("python logo", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_videos_search(self):
        """Test Brave videos search."""
        brave = BraveSearch()
        results = brave.videos("python tutorial", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_news_search(self):
        """Test Brave news search."""
        brave = BraveSearch()
        results = brave.news("python", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_suggestions(self):
        """Test Brave suggestions."""
        brave = BraveSearch()
        results = brave.suggestions("python")
        assert isinstance(results, list)


class TestYahoo:
    """Tests for Yahoo search engine."""

    @live_test
    def test_text_search(self):
        """Test Yahoo text search."""
        yahoo = YahooSearch()
        results = yahoo.text("python", max_results=2)
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_images_search(self):
        """Test Yahoo images search."""
        yahoo = YahooSearch()
        results = yahoo.images("python logo", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_videos_search(self):
        """Test Yahoo videos search."""
        yahoo = YahooSearch()
        results = yahoo.videos("python tutorial", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_news_search(self):
        """Test Yahoo news search."""
        yahoo = YahooSearch()
        results = yahoo.news("python", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_suggestions(self):
        """Test Yahoo suggestions."""
        yahoo = YahooSearch()
        results = yahoo.suggestions("python")
        assert isinstance(results, list)


class TestYep:
    """Tests for Yep search engine."""

    @live_test
    def test_text_search(self):
        """Test Yep text search."""
        yep = YepSearch()
        results = yep.text("python", max_results=2)
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_images_search(self):
        """Test Yep images search."""
        yep = YepSearch()
        results = yep.images("python logo", max_results=2)
        assert isinstance(results, list)

    @live_test
    def test_suggestions(self):
        """Test Yep suggestions."""
        yep = YepSearch()
        results = yep.suggestions("python")
        assert isinstance(results, list)


class TestStandaloneEngines:
    """Tests for standalone search engines."""

    @live_test
    def test_mojeek_search(self):
        """Test Mojeek search."""
        mojeek = Mojeek()
        results = mojeek.search("python")
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_wikipedia_search(self):
        """Test Wikipedia search."""
        wiki = Wikipedia()
        results = wiki.search("python")
        assert isinstance(results, list)
        assert len(results) >= 1

    @live_test
    def test_yandex_search(self):
        """Test Yandex search."""
        yandex = Yandex()
        results = yandex.search("python")
        assert isinstance(results, list)
        # Yandex may return empty results due to geo-blocking


class TestNotImplemented:
    """Test that unimplemented methods raise NotImplementedError."""

    def test_bing_answers_not_implemented(self):
        """Bing answers should raise NotImplementedError."""
        bing = BingSearch()
        with pytest.raises(NotImplementedError):
            bing.answers("test")

    def test_bing_maps_not_implemented(self):
        """Bing maps should raise NotImplementedError."""
        bing = BingSearch()
        with pytest.raises(NotImplementedError):
            bing.maps("test")

    def test_bing_translate_not_implemented(self):
        """Bing translate should raise NotImplementedError."""
        bing = BingSearch()
        with pytest.raises(NotImplementedError):
            bing.translate("test")

    def test_bing_videos_not_implemented(self):
        """Bing videos should raise NotImplementedError."""
        bing = BingSearch()
        with pytest.raises(NotImplementedError):
            bing.videos("test")

    def test_brave_answers_not_implemented(self):
        """Brave answers should raise NotImplementedError."""
        brave = BraveSearch()
        with pytest.raises(NotImplementedError):
            brave.answers("test")

    def test_brave_maps_not_implemented(self):
        """Brave maps should raise NotImplementedError."""
        brave = BraveSearch()
        with pytest.raises(NotImplementedError):
            brave.maps("test")

    def test_brave_translate_not_implemented(self):
        """Brave translate should raise NotImplementedError."""
        brave = BraveSearch()
        with pytest.raises(NotImplementedError):
            brave.translate("test")

    def test_yep_videos_not_implemented(self):
        """Yep videos should raise NotImplementedError."""
        yep = YepSearch()
        with pytest.raises(NotImplementedError):
            yep.videos("test")

    def test_yep_news_not_implemented(self):
        """Yep news should raise NotImplementedError."""
        yep = YepSearch()
        with pytest.raises(NotImplementedError):
            yep.news("test")

    def test_yep_answers_not_implemented(self):
        """Yep answers should raise NotImplementedError."""
        yep = YepSearch()
        with pytest.raises(NotImplementedError):
            yep.answers("test")

    def test_yep_maps_not_implemented(self):
        """Yep maps should raise NotImplementedError."""
        yep = YepSearch()
        with pytest.raises(NotImplementedError):
            yep.maps("test")

    def test_yep_translate_not_implemented(self):
        """Yep translate should raise NotImplementedError."""
        yep = YepSearch()
        with pytest.raises(NotImplementedError):
            yep.translate("test")
