"""Base class for Brave search implementations."""

from __future__ import annotations

from typing import Any, Optional

from curl_cffi.requests import Session

from ....litagent import LitAgent


class BraveBase:
    """Base class for Brave search engines."""

    def __init__(
        self,
        timeout: int = 10,
        proxies: dict[str, str] | None = None,
        verify: bool = True,
        lang: str = "en-US",
        sleep_interval: float = 0.0,
        impersonate: str = "chrome110",
    ):
        """Initialize Brave base client.

        Args:
            timeout: Timeout value for requests.
            proxies: Dictionary of proxy settings.
            verify: SSL verification flag.
            lang: Language setting.
            sleep_interval: Sleep interval between requests.
            impersonate: Browser to impersonate.
        """
        self.timeout = timeout
        self.proxies = proxies
        self.verify = verify
        self.lang = lang
        self.sleep_interval = sleep_interval
        self.base_url = "https://search.brave.com"
        from typing import cast
        self.session = Session(
            proxies=cast(Any, proxies),
            verify=verify,
            timeout=timeout,
            impersonate=cast(Any, impersonate),
        )
        self.session.headers.update(LitAgent().generate_fingerprint())
