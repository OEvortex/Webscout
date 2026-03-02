import json
from typing import Any, Dict, Optional, Union


class FakeResp:
    """A mock response object for testing."""
    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self._text = text
        self._json_data = json_data
        self.headers = headers or {}

    @property
    def text(self) -> str:
        if self._text:
            return self._text
        if self._json_data:
            return json.dumps(self._json_data)
        return ""

    def json(self) -> Any:
        if self._json_data is not None:
            return self._json_data
        return json.loads(self._text)

    def iter_lines(self):
        for line in self.text.splitlines():
            yield line.encode("utf-8")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")
