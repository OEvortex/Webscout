from __future__ import annotations

import gzip

from curl_cffi.requests import Session

from ....litagent import LitAgent


class YepBase:
    """Base class for Yep search engines."""

    def __init__(
        self,
        timeout: int = 20,
        proxies: dict[str, str] | None = None,
        verify: bool = True,
        impersonate: str | None = None,  # Kept for compatibility
    ):
        self.base_url = "https://api.yep.com/fs/2/search"
        self.timeout = timeout
        self.proxies = proxies
        self.verify = verify
        self.impersonate = impersonate or "chrome131"

        # Yep requires TLS fingerprinting bypass - must use curl_cffi with chrome131
        from typing import Any, cast
        self.session = Session(
            proxies=cast(Any, proxies),
            verify=verify,
            impersonate=cast(Any, self.impersonate),  # Required for Yep API
            timeout=timeout,
        )

        # Generate browser fingerprint and normalize header names
        fingerprint = LitAgent().generate_fingerprint()
        # Map lowercase keys to proper HTTP header case
        header_map = {
            "user_agent": "User-Agent",
            "accept_language": "Accept-Language",
            "sec_ch_ua": "sec-ch-ua",
            "platform": "Platform",
            "x_forwarded_for": "X-Forwarded-For",
            "x_real_ip": "X-Real-IP",
            "x_client_ip": "X-Client-IP",
            "forwarded": "Forwarded",
            "x_request_id": "X-Request-ID",
        }
        normalized_headers = {}
        for key, value in fingerprint.items():
            proper_key = header_map.get(key.lower(), key)
            normalized_headers[proper_key] = value

        normalized_headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://yep.com",
                "Referer": "https://yep.com/",
            }
        )
        self.session.headers.update(normalized_headers)

    def _create_session(self, headers: dict[str, str] | None = None) -> Session:
        """Create a dedicated Yep session with the configured transport settings."""
        from typing import Any, cast

        session = Session(
            proxies=cast(Any, self.proxies),
            verify=self.verify,
            impersonate=cast(Any, self.impersonate),
            timeout=self.timeout,
        )
        if headers:
            session.headers.update(headers)
        return session

    def _decompress_response(self, content: bytes) -> str:
        """Decompress gzip response if needed."""
        try:
            return gzip.decompress(content).decode("utf-8")
        except Exception:
            # Not gzipped or already decompressed
            return content.decode("utf-8", errors="replace")

