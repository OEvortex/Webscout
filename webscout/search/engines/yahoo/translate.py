"""Yahoo translate search."""

from __future__ import annotations

from .base import YahooSearchEngine


class YahooTranslate(YahooSearchEngine):
    """Yahoo translation."""

    def build_payload(self, *args, **kwargs) -> dict:
        return {}

    def run(self, *args, **kwargs) -> list[dict[str, str]]:
        """Translate text using Yahoo.

        Not supported.
        """
        raise NotImplementedError("Yahoo does not support translation")
