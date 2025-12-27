import json
import re
from decimal import Decimal
from html import unescape
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from .exceptions import WebscoutE

REGEX_STRIP_TAGS = re.compile("<.*?>")


def _expand_proxy_tb_alias(proxy: Optional[str]) -> Optional[str]:
    """Expand "tb" to a full proxy URL if applicable."""
    return "socks5://127.0.0.1:9150" if proxy == "tb" else proxy


def json_dumps(obj: Any) -> str:
    """Serialize object to JSON string.

    Args:
        obj: Object to serialize

    Returns:
        JSON string representation

    Raises:
        WebscoutE: If serialization fails
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception as ex:
        raise WebscoutE(f"{type(ex).__name__}: {ex}") from ex


def json_loads(obj: Union[str, bytes]) -> Any:
    """Deserialize JSON string to Python object.

    Args:
        obj: JSON string or bytes to deserialize

    Returns:
        Deserialized Python object

    Raises:
        WebscoutE: If deserialization fails
    """
    try:
        return json.loads(obj)
    except Exception as ex:
        raise WebscoutE(f"{type(ex).__name__}: {ex}") from ex


def _extract_vqd(html_bytes: bytes, keywords: str) -> str:
    """Extract vqd from html bytes."""
    for c1, c1_len, c2 in (
        (b'vqd="', 5, b'"'),
        (b"vqd=", 4, b"&"),
        (b"vqd='", 5, b"'"),
    ):
        try:
            start = html_bytes.index(c1) + c1_len
            end = html_bytes.index(c2, start)
            return html_bytes[start:end].decode()
        except ValueError:
            pass
    raise WebscoutE(f"_extract_vqd() {keywords=} Could not extract vqd.")


def _text_extract_json(html_bytes: bytes, keywords: str) -> List[Dict[str, str]]:
    """text(backend="api") -> extract json from html."""
    try:
        start = html_bytes.index(b"DDG.pageLayout.load('d',") + 24
        end = html_bytes.index(b");DDG.duckbar.load(", start)
        data = html_bytes[start:end]
        result: List[Dict[str, str]] = json_loads(data)
        return result
    except Exception as ex:
        raise WebscoutE(f"_text_extract_json() {keywords=} {type(ex).__name__}: {ex}") from ex
    raise WebscoutE(f"_text_extract_json() {keywords=} return None")


def _normalize(raw_html: str) -> str:
    """Strip HTML tags from the raw_html string."""
    return unescape(REGEX_STRIP_TAGS.sub("", raw_html)) if raw_html else ""


def _normalize_url(url: str) -> str:
    """Unquote URL and replace spaces with '+'."""
    return unquote(url.replace(" ", "+")) if url else ""


def _calculate_distance(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> float:
    """Calculate distance between two points in km. Haversine formula."""
    R = 6371.0087714  # Earth's radius in km
    rlat1, rlon1, rlat2, rlon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlon, dlat = rlon2 - rlon1, rlat2 - rlat1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
