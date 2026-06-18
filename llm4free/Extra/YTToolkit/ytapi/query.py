from typing import List, Optional
from urllib.parse import quote

from .channel import Channel
from .https import find_channels, find_playlists, find_videos
from .patterns import _QueryPatterns as Patterns
from .playlist import Playlist
from .utils import dup_filter, request
from .video import Video


class Search:

    @staticmethod
    def video(keywords: str) -> Optional[Video]:
        video_ids = Patterns.video_id.findall(find_videos(keywords))
        return Video(video_ids[0]) if video_ids else None

    @staticmethod
    def channel(keywords: str) -> Optional[Channel]:
        channel_ids = Patterns.channel_id.findall(find_channels(keywords))
        return Channel(channel_ids[0]) if channel_ids else None

    @staticmethod
    def playlist(keywords: str) -> Optional[Playlist]:
        playlist_ids = Patterns.playlist_id.findall(find_playlists(keywords))
        return Playlist(playlist_ids[0]) if playlist_ids else None

    @staticmethod
    def videos(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.video_id.findall(find_videos(keywords)), limit)

    @staticmethod
    def channels(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.channel_id.findall(find_channels(keywords)), limit)

    @staticmethod
    def playlists(keywords: str, limit: int = 20) -> Optional[List[str]]:
        return dup_filter(Patterns.playlist_id.findall(find_playlists(keywords)), limit)

    @staticmethod
    def shorts(keywords: str, limit: int = 20) -> Optional[List[str]]:
        """
        Search for YouTube Shorts.

        Args:
            keywords: Search query
            limit: Maximum number of results

        Returns:
            List of video IDs for matching Shorts
        """
        # sp=EgIYAQ%253D%253D is the filter for Shorts
        url = f"https://www.youtube.com/results?search_query={quote(keywords)}&sp=EgIYAQ%253D%253D"
        try:
            html = request(url)
            return dup_filter(Patterns.video_id.findall(html), limit)
        except Exception:
            return []

    @staticmethod
    def live_streams(keywords: str, limit: int = 20) -> Optional[List[str]]:
        """
        Search for live streams.

        Args:
            keywords: Search query
            limit: Maximum number of results

        Returns:
            List of video IDs for live streams
        """
        # sp=EgJAAQ%253D%253D is the filter for live streams
        url = f"https://www.youtube.com/results?search_query={quote(keywords)}&sp=EgJAAQ%253D%253D"
        try:
            html = request(url)
            return dup_filter(Patterns.video_id.findall(html), limit)
        except Exception:
            return []

    @staticmethod
    def videos_by_duration(keywords: str, duration: str = "short", limit: int = 20) -> Optional[List[str]]:
        """
        Search videos filtered by duration.

        Args:
            keywords: Search query
            duration: Duration filter - "short" (<4 min), "medium" (4-20 min), "long" (>20 min)
            limit: Maximum number of results

        Returns:
            List of video IDs
        """
        duration_filters = {
            "short": "EgIYAQ%253D%253D",    # Under 4 minutes
            "medium": "EgIYAw%253D%253D",   # 4-20 minutes
            "long": "EgIYAg%253D%253D"      # Over 20 minutes
        }
        sp = duration_filters.get(duration, "")
        url = f"https://www.youtube.com/results?search_query={quote(keywords)}&sp={sp}"
        try:
            html = request(url)
            return dup_filter(Patterns.video_id.findall(html), limit)
        except Exception:
            return []

    @staticmethod
    def videos_by_upload_date(keywords: str, when: str = "today", limit: int = 20) -> Optional[List[str]]:
        """
        Search videos filtered by upload date.

        Args:
            keywords: Search query
            when: Time filter - "hour", "today", "week", "month", "year"
            limit: Maximum number of results

        Returns:
            List of video IDs
        """
        date_filters = {
            "hour": "EgIIAQ%253D%253D",
            "today": "EgIIAg%253D%253D",
            "week": "EgIIAw%253D%253D",
            "month": "EgIIBA%253D%253D",
            "year": "EgIIBQ%253D%253D"
        }
        sp = date_filters.get(when, "")
        url = f"https://www.youtube.com/results?search_query={quote(keywords)}&sp={sp}"
        try:
            html = request(url)
            return dup_filter(Patterns.video_id.findall(html), limit)
        except Exception:
            return []


if __name__ == "__main__":
    print("Testing Search.shorts:")
    shorts = Search.shorts("funny", 5)
    print(f"  Found: {shorts}")

    print("\nTesting Search.live_streams:")
    live = Search.live_streams("music", 5)
    print(f"  Found: {live}")
