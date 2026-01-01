"""
Scout Parsers - Unified Parsing Interfaces
"""

from typing import Any, Dict, Optional, Type

from .html5lib_parser import HTML5Parser
from .html_parser import HTMLParser
from .lxml_parser import LXMLParser


class ParserRegistry:
    """
    Centralized parser registry for Scout library.
    Manages and provides access to different HTML parsing strategies.
    """

    _PARSERS: Dict[str, Type[Any]] = {
        'html.parser': HTMLParser,
        'lxml': LXMLParser,
        'html5lib': HTML5Parser
    }

    @classmethod
    def get_parser(cls, parser_name: str = 'html.parser') -> Any:
        """
        Retrieve a parser by its name.

        Args:
            parser_name (str): Name of the parser to retrieve

        Returns:
            Parser instance

        Raises:
            ValueError: If the parser is not found
        """
        if parser_name not in cls._PARSERS:
            raise ValueError(f"Parser '{parser_name}' not found. Available parsers: {list(cls._PARSERS.keys())}")

        return cls._PARSERS[parser_name]()

    @classmethod
    def register_parser(cls, name: str, parser_class: Type[Any]):
        """
        Register a new parser dynamically.

        Args:
            name (str): Name of the parser
            parser_class (Type): Parser class to register
        """
        cls._PARSERS[name] = parser_class

    @classmethod
    def list_parsers(cls) -> Dict[str, Type[Any]]:
        """
        List all registered parsers.

        Returns:
            Dict of available parsers
        """
        return cls._PARSERS.copy()

# Expose key classes and functions
__all__ = [
    'HTMLParser',
    'LXMLParser',
    'HTML5Parser',
    'ParserRegistry'
]
