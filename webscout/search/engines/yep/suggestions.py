from __future__ import annotations

from typing import Any, List

from .base import YepBase


class YepSuggestions(YepBase):
    name = "yep"
    category = "suggestions"

    _autocomplete_url = "https://api.yep.com/ac/"

    def run(self, *args, **kwargs) -> List[str]:
        keywords = args[0] if args else kwargs.get("keywords")
        region = args[1] if len(args) > 1 else kwargs.get("region", "all")

        if not keywords:
            return []

        params = {
            "query": keywords,
            "type": "web",
            "gl": region,
        }

        headers = {
            "Accept": "*/*",
            "Origin": "https://yep.com",
            "Referer": "https://yep.com/",
        }

        session = self._create_session(headers)

        try:
            response = session.get(self._autocomplete_url, params=params)
            if response.status_code in {502, 503, 504}:
                return []

            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                return self._normalize_suggestions(data[1])
            return []

        except Exception as e:
            resp = getattr(e, 'response', None)
            if resp is not None:
                if resp.status_code in {502, 503, 504}:
                    return []
                raise Exception(
                    f"Yep suggestions failed with status {resp.status_code}: {str(e)}"
                )
            raise Exception(f"Yep suggestions failed: {str(e)}")

    def _normalize_suggestions(self, suggestions: Any) -> list[str]:
        """Normalize the autocomplete payload into a simple string list."""
        if not isinstance(suggestions, list):
            return []

        normalized: list[str] = []
        for item in suggestions:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                value = item.get("q") or item.get("query") or item.get("text")
                if isinstance(value, str) and value:
                    normalized.append(value)

        return normalized

