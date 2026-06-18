from urllib.parse import quote

from .utils import request


def channel_about(head: str) -> str:
    return request(head + '/about')


def video_count(channel_id: str) -> str:
    head = 'https://www.youtube.com/results?search_query='
    tail = '&sp=EgIQAg%253D%253D'
    return request(head + channel_id + tail)


def uploads_data(head: str) -> str:
    url = head + '/videos'
    return request(url)


def streams_data(head: str) -> str:
    url = head + '/streams'
    return request(url)


def channel_playlists(head: str) -> str:
    url = head + '/playlists'
    return request(url)


def upcoming_videos(head: str) -> str:
    url = head + '/videos?view=2&live_view=502'
    return request(url)


def video_data(video_id: str) -> str:
    url = f'https://www.youtube.com/watch?v={video_id}'
    return request(url)


def playlist_data(playlist_id: str) -> str:
    url = 'https://www.youtube.com/playlist?list=' + playlist_id
    return request(url)


def trending_videos() -> str:
    return request('https://www.youtube.com/feed/trending')


def trending_songs() -> str:
    return request('https://www.youtube.com/feed/music')


def trending_games() -> str:
    return request('https://www.youtube.com/gaming')


def trending_feeds() -> str:
    return request('https://www.youtube.com/news')


def trending_streams() -> str:
    return request('https://www.youtube.com/live')


def _get_trending_learning_videos() -> str:
    return request('https://www.youtube.com/learning')


def trending_sports() -> str:
    return request('https://www.youtube.com/sports')


def find_videos(query: str) -> str:
    head = 'https://www.youtube.com/results?search_query='
    tail = '&sp=EgIQAQ%253D%253D'
    return request(head + quote(query) + tail)


def find_channels(query: str) -> str:
    head = 'https://www.youtube.com/results?search_query='
    tail = '&sp=EgIQAg%253D%253D'
    return request(head + quote(query) + tail)


def find_playlists(query: str) -> str:
    head = 'https://www.youtube.com/results?search_query='
    tail = '&sp=EgIQAw%253D%253D'
    return request(head + quote(query) + tail)
