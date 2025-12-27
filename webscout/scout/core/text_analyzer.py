"""
Scout Text Analyzer Module
"""
import re
from collections import Counter
from typing import Dict, List, Optional, Set


class ScoutTextAnalyzer:
    """
    Advanced text analysis and processing utility.
    """
    @staticmethod
    def tokenize(text: str, lowercase=True, remove_punctuation=True) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text (str): Input text
            lowercase (bool, optional): Convert to lowercase
            remove_punctuation (bool, optional): Remove punctuation

        Returns:
            List[str]: List of tokens
        """
        if lowercase:
            text = text.lower()

        if remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        return text.split()

    @staticmethod
    def count_words(text: str) -> Dict[str, int]:
        """
        Count word frequencies.

        Args:
            text (str): Input text

        Returns:
            Dict[str, int]: Word frequency dictionary
        """
        return dict(Counter(ScoutTextAnalyzer.tokenize(text)))

    @staticmethod
    def extract_entities(text: str) -> Dict[str, Set[str]]:
        """
        Extract named entities from text.

        Args:
            text (str): Input text

        Returns:
            Dict[str, Set[str]]: Extracted entities
        """
        entities = {
            'emails': set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            'urls': set(re.findall(r'https?://\S+', text)),
            'phones': set(re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)),
            'dates': set(re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text))
        }
        return entities
