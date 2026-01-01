import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from .https import channel_about, channel_playlists, streams_data, upcoming_videos, uploads_data
from .patterns import _ChannelPatterns as Patterns
from .pool import collect
from .utils import dup_filter
from .video import Video


class Channel:

    _HEAD = 'https://www.youtube.com/channel/'
    _CUSTOM = 'https://www.youtube.com/c/'
    _USER = 'https://www.youtube.com/'

    def __init__(self, channel_id: str):
        """
        Represents a YouTube channel

        Parameters
        ----------
        channel_id : str
            The id or url or custom url or user id of the channel
        """
        pattern = re.compile("UC(.+)|c/(.+)|@(.+)")
        results = pattern.findall(channel_id)
        if not results:
            self._usable_id = channel_id
            self._target_url = self._CUSTOM + channel_id
        elif results[0][0]:
            self._usable_id = results[0][0]
            self._target_url = self._HEAD + 'UC' + results[0][0]
        elif results[0][1]:
            self._usable_id = results[0][1]
            self._target_url = self._CUSTOM + results[0][1]
        elif results[0][2]:
            self._usable_id = results[0][2]
            self._target_url = self._USER + '@' + results[0][2]
        self.id = None
        self.name = None
        self.subscribers = None
        self.views = None
        self.country = None
        self.custom_url = None
        self.avatar = None
        self.banner = None
        self.url = None
        self.description = None
        self.socials = None
        self.__meta = None
        self._about_page = channel_about(self._target_url)
        self.__populate()

    def __populate(self):
        self.__meta = self.__prepare_metadata()
        if self.__meta:
            for k, v in self.__meta.items():
                setattr(self, k, v)

    def __repr__(self):
        return f'<Channel `{self._target_url}`>'

    def __prepare_metadata(self) -> Dict[str, Any]:
        """
        Returns channel metadata in a dict format

        Returns
        -------
        Dict
            Channel metadata containing the following keys:
            id, name, subscribers, views, country, custom_url, avatar, banner, url, description, socials
        """
        patterns = [
            Patterns.name,
            Patterns.avatar,
            Patterns.banner,
            Patterns.verified,
            Patterns.socials
        ]
        extracted = collect(lambda x: x.findall(self._about_page) or None, patterns)
        name, avatar, banner, verified, socials = [e[0] if e else None for e in extracted]

        # Add robust error handling for info extraction
        info_pattern = re.compile("\\[{\"aboutChannelRenderer\":(.*?)],")
        info_match = info_pattern.search(self._about_page)

        if not info_match:
            # Fallback metadata for search results or incomplete channel data
            return {
                "id": self._usable_id,
                "name": name,
                "url": self._target_url,
                "description": None,
                "country": None,
                "custom_url": None,
                "subscribers": None,
                "views": None,
                "created_at": None,
                "video_count": None,
                "avatar": avatar,
                "banner": banner,
                "verified": bool(verified),
                "socials": unquote(socials) if socials is not None else None
            }

        try:
            info_str = info_match.group(1) + "]}}}}"
            info = json.loads(info_str)["metadata"]["aboutChannelViewModel"]

            return {
                "id": info.get("channelId", self._usable_id),
                "name": name,
                "url": "https://www.youtube.com/channel/" + info.get("channelId", self._usable_id),
                "description": info.get("description"),
                "country": info.get("country"),
                "custom_url": info.get("canonicalChannelUrl"),
                "subscribers": info.get("subscriberCountText", "").split(' ')[0] if "subscriberCountText" in info else None,
                "views": info.get("viewCountText", "").replace(' views', '') if "viewCountText" in info else None,
                "created_at": info.get("joinedDateText", {}).get("content", "").replace('Joined ', '') if "joinedDateText" in info else None,
                "video_count": info.get("videoCountText", "").split(' ')[0] if "videoCountText" in info else None,
                "avatar": avatar,
                "banner": banner,
                "verified": bool(verified),
                "socials": unquote(socials) if socials is not None else None
            }
        except (KeyError, json.JSONDecodeError):
            # Fallback if JSON parsing fails
            return {
                "id": self._usable_id,
                "name": name,
                "url": self._target_url,
                "description": None,
                "country": None,
                "custom_url": None,
                "subscribers": None,
                "views": None,
                "created_at": None,
                "video_count": None,
                "avatar": avatar,
                "banner": banner,
                "verified": bool(verified),
                "socials": unquote(socials) if socials is not None else None
            }

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """
        Returns channel metadata in a dict format

        Returns
        -------
        Dict
            Channel metadata containing the following keys:
            id, name, subscribers, views, country, custom_url, avatar, banner, url, description, socials etc.
        """
        return self.__meta

    @property
    def live(self) -> bool:
        """
        Checks if the channel is live

        Returns
        -------
        bool
            True if the channel is live
        """
        return bool(self.current_streams)

    @property
    def streaming_now(self) -> Optional[str]:
        """
        Fetches the id of currently streaming video

        Returns
        -------
        str | None
            The id of the currently streaming video or None
        """
        streams = self.current_streams
        return streams[0] if streams else None

    @property
    def current_streams(self) -> Optional[List[str]]:
        """
        Fetches the ids of all ongoing streams

        Returns
        -------
        List[str] | None
            The ids of all ongoing streams or None
        """
        raw = streams_data(self._target_url)
        filtered_ids = dup_filter(Patterns.stream_ids.findall(raw))
        if not filtered_ids:
            return None
        return [id_ for id_ in filtered_ids if f"vi/{id_}/hqdefault_live.jpg" in raw]

    @property
    def old_streams(self) -> Optional[List[str]]:
        """
        Fetches the ids of all old or completed streams

        Returns
        -------
        List[str] | None
            The ids of all old or completed streams or None
        """
        raw = streams_data(self._target_url)
        filtered_ids = dup_filter(Patterns.stream_ids.findall(raw))
        if not filtered_ids:
            return None
        return [id_ for id_ in filtered_ids if f"vi/{id_}/hqdefault_live.jpg" not in raw]

    @property
    def last_streamed(self) -> Optional[str]:
        """
        Fetches the id of the last completed livestream

        Returns
        -------
        str | None
            The id of the last livestreamed video or None
        """
        ids = self.old_streams
        return ids[0] if ids else None

    def uploads(self, limit: int = 20) -> Optional[List[str]]:
        """
        Fetches the ids of all uploaded videos

        Parameters
        ----------
        limit : int
            The number of videos to fetch, defaults to 20

        Returns
        -------
        List[str] | None
            The ids of uploaded videos or None
        """
        return dup_filter(Patterns.upload_ids.findall(uploads_data(self._target_url)), limit)

    @property
    def last_uploaded(self) -> Optional[str]:
        """
        Fetches the id of the last uploaded video

        Returns
        -------
        str | None
            The id of the last uploaded video or None
        """
        ids = self.uploads()
        return ids[0] if ids else None

    @property
    def upcoming(self) -> Optional[Video]:
        """
        Fetches the upcoming video

        Returns
        -------
        Video | None
            The upcoming video or None
        """
        raw = upcoming_videos(self._target_url)
        if not Patterns.upcoming_check.search(raw):
            return None
        upcoming = Patterns.upcoming.findall(raw)
        return Video(upcoming[0]) if upcoming else None

    @property
    def upcomings(self) -> Optional[List[str]]:
        """
        Fetches the upcoming videos

        Returns
        -------
        List[str] | None
            The ids of upcoming videos or None
        """
        raw = upcoming_videos(self._target_url)
        if not Patterns.upcoming_check.search(raw):
            return None
        video_ids = Patterns.upcoming.findall(raw)
        return video_ids

    @property
    def playlists(self) -> Optional[List[str]]:
        """
        Fetches the ids of all playlists

        Returns
        -------
        List[str] | None
            The ids of all playlists or None
        """
        return dup_filter(Patterns.playlists.findall(channel_playlists(self._target_url)))
