"""
Utility functions - making life easier! 🛠️
"""

from typing import Optional, Union


def decode_markup(markup: Union[str, bytes], encoding: Optional[str] = None) -> str:
    """
    Decode that markup - no encoding drama! 🎯

    Args:
        markup: The raw HTML/XML content
        encoding: The encoding to use (if known)

    Returns:
        Clean decoded string ready for parsing! ✨
    """
    if isinstance(markup, str):
        return markup

    if encoding:
        try:
            return markup.decode(encoding)
        except UnicodeDecodeError:
            pass

    # Try common encodings - we got options! 💪
    encodings = ["utf-8", "latin1", "iso-8859-1", "ascii"]

    for enc in encodings:
        try:
            return markup.decode(enc)
        except UnicodeDecodeError:
            continue

    # Last resort - ignore errors and keep it moving! 🚀
    return markup.decode("utf-8", errors="ignore")
