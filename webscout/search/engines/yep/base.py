from __future__ import annotations

from curl_cffi.requests import Session

from ....litagent import LitAgent


class YepBase:
    """Base class for Yep search engines."""

    def __init__(
        self,
        timeout: int = 20,
        proxies: dict[str, str] | None = None,
        verify: bool = True,
        impersonate: str = "chrome110",
    ):
        self.base_url = "https://api.yep.com/fs/2/search"
        self.timeout = timeout
        from typing import Any, Optional, cast
        self.session = Session(
            proxies=cast(Any, proxies),
            verify=verify,
            impersonate=cast(Any, impersonate),
            timeout=timeout,
        )
        self.session.headers.update(
            {
                **LitAgent().generate_fingerprint(),
                "Origin": "https://yep.com",
                "Referer": "https://yep.com/",
            }
        )

