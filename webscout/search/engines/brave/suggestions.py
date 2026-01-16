"""Brave search suggestions/autocomplete implementation.

This module provides access to Brave Search's autocomplete/suggestions API
that returns search suggestions as users type.

Example:
    >>> from webscout.search.engines.brave.suggestions import BraveSuggestions
    >>> suggester = BraveSuggestions()
    >>> suggestions = suggester.run("pyth")
    >>> for suggestion in suggestions:
    ...     print(suggestion.query)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .base import BraveBase


@dataclass
class SuggestionResult:
    """A single search suggestion result.

    Attributes:
        query: The suggested search query.
        is_entity: Whether this suggestion represents a known entity.
        name: Display name for entities.
        desc: Description for entities.
        category: Category of the entity (e.g., 'company', 'application').
        image: URL to entity image/logo if available.
        is_logo: Whether the image is a logo.
    """

    query: str = ""
    is_entity: bool = False
    name: str = ""
    desc: str = ""
    category: str = ""
    image: str = ""
    is_logo: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the suggestion.
        """
        return {
            "query": self.query,
            "is_entity": self.is_entity,
            "name": self.name,
            "desc": self.desc,
            "category": self.category,
            "image": self.image,
            "is_logo": self.is_logo,
        }


@dataclass
class SuggestionsResponse:
    """Response containing search suggestions.

    Attributes:
        query: The original query that was submitted.
        suggestions: List of suggestion results.
    """

    query: str = ""
    suggestions: list[SuggestionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "query": self.query,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


class BraveSuggestions(BraveBase):
    """Brave search suggestions/autocomplete engine.

    Fetches search suggestions from Brave's autocomplete API endpoint.
    Supports both simple suggestions and rich entity suggestions with
    additional metadata like descriptions, categories, and images.

    Attributes:
        name: Engine identifier name.
        provider: Provider identifier.
        category: Search category type.
        api_url: URL for the suggestions API endpoint.
    """

    name = "brave_suggestions"
    provider = "brave"
    category = "suggestions"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize Brave suggestions client.

        Args:
            *args: Positional arguments passed to BraveBase.
            **kwargs: Keyword arguments passed to BraveBase.
        """
        super().__init__(*args, **kwargs)
        self.api_url = f"{self.base_url}/api/suggest"

    def run(
        self,
        query: str,
        rich: bool = True,
        country: str | None = None,
        source: str = "web",
        max_results: int | None = None,
    ) -> list[SuggestionResult]:
        """Get search suggestions for a query.

        Args:
            query: The partial search query to get suggestions for.
            rich: Whether to include rich entity information (default True).
            country: Country code for localized suggestions (e.g., 'us', 'in').
            source: Search source type (default 'web').
            max_results: Maximum number of suggestions to return.

        Returns:
            List of SuggestionResult objects containing suggestions.

        Raises:
            ValueError: If no query is provided.
            Exception: If the API request fails.
        """
        if not query:
            raise ValueError("Query is mandatory")

        params: dict[str, str] = {
            "q": query,
            "source": source,
        }

        if rich:
            params["rich"] = "true"

        if country:
            params["country"] = country

        response_data = self._fetch_suggestions(params)
        suggestions = self._parse_response(response_data)

        if max_results is not None:
            suggestions = suggestions[:max_results]

        return suggestions

    def suggest(
        self,
        query: str,
        rich: bool = True,
        country: str | None = None,
    ) -> SuggestionsResponse:
        """Get search suggestions with full response object.

        This method returns a SuggestionsResponse object containing
        both the original query and the list of suggestions.

        Args:
            query: The partial search query to get suggestions for.
            rich: Whether to include rich entity information.
            country: Country code for localized suggestions.

        Returns:
            SuggestionsResponse object with query and suggestions.
        """
        suggestions = self.run(query, rich=rich, country=country)
        return SuggestionsResponse(query=query, suggestions=suggestions)

    def _fetch_suggestions(self, params: dict[str, str]) -> list[Any]:
        """Fetch suggestions from the Brave API.

        Args:
            params: Query parameters for the API request.

        Returns:
            Raw JSON response as a list.

        Raises:
            Exception: If the request fails.
        """
        headers = dict(self.session.headers) if getattr(self, "session", None) else {}
        headers.update({
            "Referer": "https://search.brave.com/",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })

        try:
            resp = self.session.get(
                self.api_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse suggestions response: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to fetch suggestions: {e}") from e

    def _parse_response(self, data: list[Any]) -> list[SuggestionResult]:
        """Parse the API response into SuggestionResult objects.

        The Brave suggestions API returns data in the format:
        ["query", [suggestion_objects]]

        Each suggestion object can be either:
        - Simple: {"is_entity": false, "q": "query text"}
        - Entity: {"is_entity": true, "q": "query", "name": "...", "desc": "...",
                   "category": "...", "img": "...", "logo": true}

        Args:
            data: Raw JSON response from the API.

        Returns:
            List of SuggestionResult objects.
        """
        results: list[SuggestionResult] = []

        if not data or len(data) < 2:
            return results

        # Second element contains the suggestions list
        suggestions_list = data[1] if len(data) > 1 else []

        for item in suggestions_list:
            if not isinstance(item, dict):
                continue

            query_text = item.get("q", "")
            is_entity = item.get("is_entity", False)

            result = SuggestionResult(
                query=query_text,
                is_entity=is_entity,
                name=item.get("name", ""),
                desc=item.get("desc", ""),
                category=item.get("category", ""),
                image=item.get("img", ""),
                is_logo=item.get("logo", False),
            )

            results.append(result)

        return results

    def get_simple_suggestions(self, query: str, max_results: int = 10) -> list[str]:
        """Get a simple list of suggestion strings.

        This is a convenience method that returns just the query strings
        without the full SuggestionResult objects.

        Args:
            query: The partial search query to get suggestions for.
            max_results: Maximum number of suggestions to return.

        Returns:
            List of suggestion query strings.
        """
        suggestions = self.run(query, rich=False, max_results=max_results)
        return [s.query for s in suggestions if s.query]


if __name__ == "__main__":
    # Test the BraveSuggestions
    print("Testing BraveSuggestions...")

    suggester = BraveSuggestions(timeout=10)

    try:
        # Test basic suggestions
        print("\n--- Testing with 'pyth' ---")
        results = suggester.run("pyth")

        print(f"Found {len(results)} suggestions:\n")
        for i, suggestion in enumerate(results, 1):
            if suggestion.is_entity:
                print(f"{i}. [ENTITY] {suggestion.query}")
                print(f"   Name: {suggestion.name}")
                print(f"   Description: {suggestion.desc}")
                print(f"   Category: {suggestion.category}")
                if suggestion.image:
                    print(f"   Image: {suggestion.image[:60]}...")
            else:
                print(f"{i}. {suggestion.query}")
            print()

        # Test simple suggestions
        print("\n--- Testing simple suggestions with 'java' ---")
        simple = suggester.get_simple_suggestions("java", max_results=5)
        print("Simple suggestions:")
        for s in simple:
            print(f"  - {s}")

        # Test full response object
        print("\n--- Testing full response with 'react' ---")
        response = suggester.suggest("react")
        print(f"Query: {response.query}")
        print(f"Suggestions count: {len(response.suggestions)}")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
