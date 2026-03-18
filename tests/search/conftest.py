"""Pytest configuration for search engine tests."""

from __future__ import annotations

from collections.abc import Sequence

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: Sequence[pytest.Item]) -> None:
    """Skip live search tests unless the live marker is requested explicitly."""
    markexpr = config.option.markexpr or ""
    live_enabled = "live" in markexpr

    if live_enabled:
        return

    skip_live = pytest.mark.skip(reason="Live search tests are skipped unless -m live is used.")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
