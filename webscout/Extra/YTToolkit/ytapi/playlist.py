import re
from typing import Any, Dict, Optional

from .https import playlist_data
from .patterns import _PlaylistPatterns as Patterns
from .pool import collect
from .utils import dup_filter


class Playlist:

    def __init__(self, playlist_id: str):
        """
        Represents a YouTube Playlist

        Parameters
        ----------
        playlist_id : str
            The id or url of the playlist
        """
        pattern = re.compile('=(.+?)$|^PL(.+?)$')
        match = pattern.search(playlist_id)
        if not match:
            raise ValueError(f'Invalid playlist id: {playlist_id}')
        if match.group(1):
            self.id = match.group(1)
        elif match.group(2):
            self.id = 'PL' + match.group(2)
        self._playlist_data = playlist_data(self.id)

    def __repr__(self):
        return f'<Playlist {self.id}>'

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Fetches playlist metadata in a dict format

        Returns
        -------
        Dict
            Playlist metadata in a dict format containing keys: id, url, name, video_count, thumbnail,
        """
        patterns = [
            Patterns.name,
            Patterns.video_count,
            Patterns.thumbnail,
            Patterns.video_id,
        ]
        ext = collect(lambda x: x.findall(self._playlist_data) or None, patterns)
        data = [e[0] if e else None for e in ext]
        return {
            'id': self.id,
            'url': 'https://www.youtube.com/playlist?list=' + self.id,
            'name': data[0] if data else None,
            'video_count': data[1] if data else None,
            'thumbnail': data[2] if data else None,
            'videos': dup_filter(ext[3])
        }
