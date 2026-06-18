"""Yahoo answers search."""

from __future__ import annotations

from .base import YahooSearchEngine


class YahooAnswers(YahooSearchEngine):
    """Yahoo instant answers."""

    def build_payload(self, *args, **kwargs) -> dict:
        return {}

    def run(self, *args, **kwargs) -> list[dict[str, str]]:
        """Get instant answers from Yahoo.

        Not supported.
        """
        raise NotImplementedError("Yahoo does not support instant answers")
