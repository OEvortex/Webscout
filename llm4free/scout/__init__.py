"""
Scout: A powerful, zero-dependency web scraping library
"""

from .core import Scout, ScoutCrawler, ScoutSearchResult, ScoutTextAnalyzer, ScoutWebAnalyzer
from .element import NavigableString, Tag

__all__ = ['Scout', 'ScoutCrawler', 'Tag', 'NavigableString','ScoutTextAnalyzer', 'ScoutWebAnalyzer', 'ScoutSearchResult']
