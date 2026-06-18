import re


class _ChannelPatterns:
    name = re.compile(r'channelMetadataRenderer\":{\"title\":\"(.*?)\"')
    id = re.compile(r'channelId\":\"(.*?)\"')
    verified = re.compile(r'"label":"Verified"')
    check_live = re.compile(r'{"text":"LIVE"}')
    live = re.compile(r"thumbnailOverlays\":\[(.*?)]")
    video_id = re.compile(r'videoId\":\"(.*?)\"')
    uploads = re.compile(r"gridVideoRenderer\":{\"videoId\":\"(.*?)\"")
    subscribers = re.compile(r"\"subscriberCountText\":{\"accessibility\":(.*?),")
    views = re.compile(r"viewCountText\":{\"simpleText\":\"(.*?)\"}")
    creation = re.compile(r"{\"text\":\"Joined \"},{\"text\":\"(.*?)\"}")
    country = re.compile(r"country\":{\"simpleText\":\"(.*?)\"}")
    custom_url = re.compile(r"canonicalChannelUrl\":\"(.*?)\"")
    description = re.compile(r"{\"description\":{\"simpleText\":\"(.*?)\"}")
    avatar = re.compile(r"height\":88},{\"url\":\"(.*?)\"")
    banner = re.compile(r"width\":1280,\"height\":351},{\"url\":\"(.*?)\"")
    playlists = re.compile(r"{\"url\":\"/playlist\?list=(.*?)\"")
    video_count = re.compile(r"videoCountText\":{\"runs\":\[{\"text\":(.*?)}")
    socials = re.compile(r"q=https%3A%2F%2F(.*?)\"")
    upload_ids = re.compile(r"videoId\":\"(.*?)\"")
    stream_ids = re.compile(r"videoId\":\"(.*?)\"")
    upload_chunk = re.compile(r"gridVideoRenderer\":{(.*?)\"navigationEndpoint")
    upload_chunk_fl_1 = re.compile(r"simpleText\":\"Streamed")
    upload_chunk_fl_2 = re.compile(r"default_live.")
    upcoming_check = re.compile(r"\"title\":\"Upcoming live streams\"")
    upcoming = re.compile(r"gridVideoRenderer\":{\"videoId\":\"(.*?)\"")


class _VideoPatterns:
    video_id = re.compile(r'videoId\":\"(.*?)\"')
    title = re.compile(r"title\":\"(.*?)\"")
    duration = re.compile(r"approxDurationMs\":\"(.*?)\"")
    upload_date = re.compile(r"uploadDate\":\"(.*?)\"")
    author_id = re.compile(r"channelIds\":\[\"(.*?)\"")
    description = re.compile(r"shortDescription\":\"(.*)\",\"isCrawlable")
    tags = re.compile(r"<meta name=\"keywords\" content=\"(.*?)\">")
    is_streamed = re.compile(r"simpleText\":\"Streamed live")
    is_premiered = re.compile(r"dateText\":{\"simpleText\":\"Premiered")
    views = re.compile(r"videoViewCountRenderer\":{\"viewCount\":{\"simpleText\":\"(.*?)\"")
    likes = re.compile(r"toggledText\":{\"accessibility\":{\"accessibilityData\":{\"label\":\"(.*?) ")
    thumbnail = re.compile(r"playerMicroformatRenderer\":{\"thumbnail\":{\"thumbnails\":\[{\"url\":\"(.*?)\"")


class _PlaylistPatterns:
    name = re.compile(r"{\"title\":\"(.*?)\"")
    video_count = re.compile(r"stats\":\[{\"runs\":\[{\"text\":\"(.*?)\"")
    video_id = re.compile(r"videoId\":\"(.*?)\"")
    thumbnail = re.compile(r"og:image\" content=\"(.*?)\?")


class _ExtraPatterns:
    video_id = re.compile(r"videoId\":\"(.*?)\"")


class _QueryPatterns:
    channel_id = re.compile(r"channelId\":\"(.*?)\"")
    video_id = re.compile(r"videoId\":\"(.*?)\"")
    playlist_id = re.compile(r"playlistId\":\"(.*?)\"")
