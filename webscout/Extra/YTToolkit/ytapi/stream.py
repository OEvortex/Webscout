import re
from typing import Any, Dict, Optional

from .https import video_data
from .patterns import _VideoPatterns as Patterns
from .pool import collect


class Video:

    _HEAD = 'https://www.youtube.com/watch?v='

    def __init__(self, video_id: str):
        pattern = re.compile(r'.be/(.*?)$|=(.*?)$|^(\w{11})$')  # noqa
        match = pattern.search(video_id)
        if match:
            self._matched_id = (
                    match.group(1)
                    or match.group(2)
                    or match.group(3)
            )
        else:
            self._matched_id = None

        if self._matched_id:
            self._url = self._HEAD + self._matched_id
            self._video_data = video_data(self._matched_id)
        else:
            raise ValueError('invalid video id or url')

    def __repr__(self):
        return f'<Video {self._url}>'

    @property
    def metadata(self) -> Dict[str, Any]:
        patterns = [
            Patterns.title,
            Patterns.views,
            Patterns.likes,
            Patterns.duration,
            Patterns.author_id,
            Patterns.upload_date,
            Patterns.thumbnail,
            Patterns.tags,
            Patterns.description,
            Patterns.is_streamed,
            Patterns.is_premiered
        ]
        ext = collect(lambda x: x.findall(self._video_data) or None, patterns)
        data = [i[0] if i else i for i in ext]
        return {
            'title': data[0],
            'id': self._matched_id,
            'views': data[1][:-6] if data[1] else None,
            'likes': data[2],
            'streamed': data[9] is not None,
            'premiered': data[10],
            'duration': int(data[3]) / 1000 if data[3] else None,
            'author': data[4],
            'upload_date': data[5],
            'url': self._url,
            'thumbnail': data[6],
            'tags': data[7].split(',') if data[7] else None,
            'description': data[8].replace('\\n', '\n') if data[8] else None
        }

if __name__ == '__main__':
    print(Video('https://www.youtube.com/watch?v=9bZkp7q19f0').metadata)
