from typing import List, Optional

from .https import (
    _get_trending_learning_videos,
    trending_feeds,
    trending_games,
    trending_songs,
    trending_sports,
    trending_streams,
    trending_videos,
)
from .patterns import _ExtraPatterns as Patterns
from .utils import dup_filter, request


class Extras:

    @staticmethod
    def trending_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.trending_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        data = Patterns.video_id.findall(trending_videos())
        return dup_filter(data, limit) if data else None

    @staticmethod
    def music_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending music videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.music_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        data = Patterns.video_id.findall(trending_songs())
        return dup_filter(data, limit) if data else None

    @staticmethod
    def gaming_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending gaming videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.gaming_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        return dup_filter(Patterns.video_id.findall(trending_games()), limit)

    @staticmethod
    def news_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending news videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.news_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        return dup_filter(Patterns.video_id.findall(trending_feeds()), limit)

    @staticmethod
    def live_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending live videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.live_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        return dup_filter(Patterns.video_id.findall(trending_streams()), limit)

    @staticmethod
    def educational_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending educational videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.educational_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        return dup_filter(Patterns.video_id.findall(_get_trending_learning_videos()), limit)

    @staticmethod
    def sport_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending sports videos from YouTube.

        Args:
            limit (int, optional): Maximum number of videos to return.
                                  Alternatively, manual slicing can be used:
                                  Extras.sport_videos()[:5]

        Returns:
            Optional[List[str]]: List of video IDs or None if no videos found
        """
        return dup_filter(Patterns.video_id.findall(trending_sports()), limit)

    @staticmethod
    def shorts_videos(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending YouTube Shorts.

        Args:
            limit (int, optional): Maximum number of Shorts to return.

        Returns:
            Optional[List[str]]: List of video IDs or None if no Shorts found
        """
        try:
            html = request("https://www.youtube.com/shorts")
            video_ids = Patterns.video_id.findall(html)
            return dup_filter(video_ids, limit) if video_ids else None
        except Exception:
            return None

    @staticmethod
    def movies(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get featured movies from YouTube.

        Args:
            limit (int, optional): Maximum number of movies to return.

        Returns:
            Optional[List[str]]: List of video IDs or None if no movies found
        """
        try:
            html = request("https://www.youtube.com/feed/storefront")
            video_ids = Patterns.video_id.findall(html)
            return dup_filter(video_ids, limit) if video_ids else None
        except Exception:
            return None

    @staticmethod
    def podcasts(limit: Optional[int] = None) -> Optional[List[str]]:
        """
        Get trending podcasts from YouTube.

        Args:
            limit (int, optional): Maximum number of podcasts to return.

        Returns:
            Optional[List[str]]: List of video IDs or None if no podcasts found
        """
        try:
            html = request("https://www.youtube.com/podcasts")
            video_ids = Patterns.video_id.findall(html)
            return dup_filter(video_ids, limit) if video_ids else None
        except Exception:
            return None

