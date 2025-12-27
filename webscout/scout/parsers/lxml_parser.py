"""
Scout LXML Parser - Advanced HTML/XML Parsing with lxml
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..element import NavigableString, Tag

# lxml is an optional dependency; import lazily at runtime to avoid hard dependency for type checking
etree = None  # type: ignore
lxml_html = None  # type: ignore


class LXMLParser:
    """
    Advanced HTML/XML parser using lxml library.
    Provides robust parsing with enhanced error handling and flexibility.
    """

    def __init__(self, parser_type: str = 'html'):
        """
        Initialize the LXML parser with advanced parsing capabilities.

        Args:
            parser_type (str): Type of parser ('html' or 'xml')
        """
        self._parser_type = parser_type
        self._parsing_errors = []

        # Select appropriate parser based on type
        import importlib
        global lxml_html, etree

        if parser_type == 'html':
            if lxml_html is None:
                try:
                    # Import lazily so lxml remains optional
                    lxml_html = importlib.import_module("lxml.html")
                except Exception as e:
                    raise ImportError("lxml is required for HTML parsing") from e
            self._parser = lxml_html.HTMLParser(recover=True, encoding='utf-8')
        elif parser_type == 'xml':
            if etree is None:
                try:
                    etree = importlib.import_module("lxml.etree")
                except Exception as e:
                    raise ImportError("lxml is required for XML parsing") from e
            self._parser = etree.XMLParser(recover=True, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")

    def parse(self, markup: str) -> Tag:
        """
        Parse HTML/XML markup and return the root tag.

        Args:
            markup (str): HTML/XML content to parse

        Returns:
            Tag: Parsed document root
        """
        try:
            # Preprocess markup to handle common issues
            markup = self._preprocess_markup(markup)

            # Parse the markup
            if self._parser_type == 'html':
                assert lxml_html is not None
                tree = lxml_html.fromstring(markup, parser=self._parser)
            else:
                assert etree is not None
                tree = etree.fromstring(markup, parser=self._parser)

            # Convert lxml element to Scout Tag
            return self._convert_element(tree)

        except Exception as e:
            self._parsing_errors.append(str(e))
            return Tag('root')

    def _preprocess_markup(self, markup: str) -> str:
        """
        Preprocess markup to handle common parsing issues.

        Args:
            markup (str): Raw markup

        Returns:
            str: Preprocessed markup
        """
        # Remove XML/HTML comments
        markup = re.sub(r'<!--.*?-->', '', markup, flags=re.DOTALL)

        # Handle unclosed tags for HTML
        if self._parser_type == 'html':
            markup = re.sub(r'<(br|img|input|hr|meta)([^>]*?)(?<!/)>', r'<\1\2 />', markup, flags=re.IGNORECASE)

        return markup

    def _convert_element(self, element: Any) -> Tag:
        """
        Convert lxml element to Scout Tag.

        Args:
            element (etree._Element or lxml_html.HtmlElement): lxml element

        Returns:
            Tag: Converted Scout Tag
        """
        # Create Tag with name and attributes
        # Strip namespaces like {http://www.w3.org/1999/xhtml}div
        tag_name = element.tag
        if '}' in tag_name:
            tag_name = tag_name.split('}', 1)[1]

        tag = Tag(tag_name, dict(element.attrib))

        # Add text content
        if element.text:
            tag.contents.append(NavigableString(element.text))

        # Recursively add child elements
        for child in element:
            child_tag = self._convert_element(child)
            child_tag.parent = tag
            tag.contents.append(child_tag)

            # Add tail text
            if child.tail:
                tail_text = NavigableString(child.tail)
                tail_text.parent = tag
                tag.contents.append(tail_text)

        return tag

    def get_parsing_errors(self) -> List[str]:
        """
        Retrieve parsing errors encountered during processing.

        Returns:
            List[str]: List of parsing error messages
        """
        return self._parsing_errors

    def find_all(self, markup: str, tag: Optional[Union[str, List[str]]] = None,
                 attrs: Optional[Dict[str, Any]] = None,
                 recursive: bool = True,
                 text: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Tag]:
        """
        Find all matching elements in the parsed document.

        Args:
            markup (str): HTML/XML content to parse
            tag (str or List[str], optional): Tag name(s) to search for
            attrs (dict, optional): Attribute filters
            recursive (bool): Whether to search recursively
            text (str, optional): Text content to search for
            limit (int, optional): Maximum number of results

        Returns:
            List[Tag]: List of matching tags
        """
        root = self.parse(markup)

        def matches(element: Tag) -> bool:
            """Check if an element matches search criteria."""
            # Tag filter
            if tag and isinstance(tag, str) and element.name != tag:
                return False
            if tag and isinstance(tag, list) and element.name not in tag:
                return False

            # Attribute filter
            if attrs:
                for key, value in attrs.items():
                    if key not in element.attrs or element.attrs[key] != value:
                        return False

            # Text filter
            if text:
                element_text = ' '.join([str(c) for c in element.contents if isinstance(c, NavigableString)])
                if text not in element_text:
                    return False

            return True

        def collect_matches(element: Tag, results: List[Tag]):
            """Recursively collect matching elements."""
            if matches(element):
                results.append(element)
                if limit and len(results) >= limit:
                    return

            if recursive:
                for child in element.contents:
                    if isinstance(child, Tag):
                        collect_matches(child, results)

        results = []
        collect_matches(root, results)
        return results
