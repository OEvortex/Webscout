"""YouTube Hashtag functionality."""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .patterns import _ExtraPatterns as Patterns
from .utils import dup_filter, request


class Hashtag:
    """Class for YouTube hashtag operations."""

    BASE_URL = "https://www.youtube.com/hashtag"

    @staticmethod
    def get_videos(tag: str, limit: int = 20) -> List[str]:
        """
        Get videos associated with a hashtag.

        Args:
            tag: Hashtag (with or without #)
            limit: Maximum number of videos to return

        Returns:
            List of video IDs
        """
        if not tag:
            return []

        # Remove # if present and clean the tag
        tag = tag.lstrip('#').strip().lower()
        tag = re.sub(r'[^a-zA-Z0-9]', '', tag)

        if not tag:
            return []

        url = f"{Hashtag.BASE_URL}/{quote(tag)}"

        try:
            html = request(url)
            video_ids = Patterns.video_id.findall(html)
            return dup_filter(video_ids, limit)
        except Exception:
            return []

    @staticmethod
    def get_metadata(tag: str) -> Dict[str, Any]:
        """
        Get metadata about a hashtag.

        Args:
            tag: Hashtag (with or without #)

        Returns:
            Dictionary with hashtag info (name, video_count if available)
        """
        if not tag:
            return {}

        tag = tag.lstrip('#').strip().lower()
        tag = re.sub(r'[^a-zA-Z0-9]', '', tag)

        if not tag:
            return {}

        url = f"{Hashtag.BASE_URL}/{quote(tag)}"

        try:
            html = request(url)

            # Try to extract video count if available
            video_count_match = re.search(r'"videoCountText":\s*\{\s*"runs":\s*\[\s*\{\s*"text":\s*"([^"]+)"', html)
            video_count = video_count_match.group(1) if video_count_match else None

            # Get sample of videos
            video_ids = Patterns.video_id.findall(html)

            return {
                'tag': tag,
                'url': url,
                'video_count': video_count,
                'sample_videos': dup_filter(video_ids, 10)
            }
        except Exception:
            return {'tag': tag, 'url': url}

    @staticmethod
    def extract_from_text(text: str) -> List[str]:
        """
        Extract hashtags from text.

        Args:
            text: Text containing hashtags

        Returns:
            List of hashtags found
        """
        if not text:
            return []

        pattern = r'#([a-zA-Z0-9_]+)'
        matches = re.findall(pattern, text)
        return list(dict.fromkeys(matches))  # Remove duplicates, preserve order


if __name__ == "__main__":
    print("Testing Hashtag.get_videos:")
    videos = Hashtag.get_videos("python", 5)
    for vid in videos:
        print(f"  - {vid}")

    print("\nHashtag metadata:")
    meta = Hashtag.get_metadata("coding")
    print(f"  Tag: {meta.get('tag')}")
    print(f"  Videos: {len(meta.get('sample_videos', []))}")

    print("\nExtract hashtags:")
    text = "Check out my new #python #tutorial for #beginners!"
    tags = Hashtag.extract_from_text(text)
    print(f"  Found: {tags}")
