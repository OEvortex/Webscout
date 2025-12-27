"""
Scout Search Result Module
"""

from typing import Any, Callable, Dict, List, Optional

from ..element import Tag
from .text_analyzer import ScoutTextAnalyzer


class ScoutSearchResult(list):
    """
    Represents a search result that behaves like a list but with advanced
    querying capabilities. Highly compatible with BS4 ResultSet.
    """

    def __init__(self, results: List[Tag]):
        """
        Initialize a search result collection.

        Args:
            results (List[Tag]): List of matching tags
        """
        super().__init__(results)

    def texts(self, separator=" ", strip=True) -> List[str]:
        """Extract texts from all results."""
        return [tag.get_text(separator, strip) for tag in self]

    def attrs(self, attr_name: str) -> List[Any]:
        """Extract a specific attribute from all results."""
        return [tag.get(attr_name) for tag in self]

    def filter(self, predicate: Callable[[Tag], bool]) -> "ScoutSearchResult":
        """Filter results using a predicate function."""
        return ScoutSearchResult([tag for tag in self if predicate(tag)])

    def map(self, transform: Callable[[Tag], Any]) -> List[Any]:
        """Transform results using a mapping function."""
        return [transform(tag) for tag in self]

    def analyze_text(self) -> Dict[str, Any]:
        """Perform text analysis on search results."""
        texts = self.texts(strip=True)
        full_text = " ".join(texts)

        return {
            "total_results": len(self),
            "word_count": ScoutTextAnalyzer.count_words(full_text),
            "entities": ScoutTextAnalyzer.extract_entities(full_text),
        }
