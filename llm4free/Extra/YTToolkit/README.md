<div align="center">
  <a href="https://github.com/pyscout/LLM4Free">
    <img src="https://img.shields.io/badge/YTToolkit-YouTube%20Toolkit-red?style=for-the-badge&logo=youtube&logoColor=white" alt="YTToolkit Logo">
  </a>
  <h1>YTToolkit</h1>
  <p><strong>Comprehensive YouTube Toolkit for Downloading, Transcription, and Data Extraction</strong></p>

  <!-- Badges -->
  <p>
    <a href="https://pypi.org/project/llm4free/"><img src="https://img.shields.io/pypi/v/llm4free.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="#"><img src="https://img.shields.io/badge/No%20API%20Key-Required-success?style=flat-square" alt="No API Key Required"></a>
    <a href="#"><img src="https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python" alt="Python Version"></a>
  </p>
</div>

> [!NOTE]
> YTToolkit provides a complete suite of YouTube tools including video downloading, transcript extraction, and comprehensive data retrieval - all without requiring an official API key.

## ✨ Features

### Video Management

* **Advanced Video Downloading**
  * Multiple format support (MP4, MP3)
  * Customizable quality selection (up to 4K)
  * Progress tracking and auto-save functionality
  * Batch downloading with search capabilities

* **Transcript Extraction** (InnerTube API)
  * Multi-language transcript support
  * Automatic and manual transcript fetching
  * Real-time translation capabilities
  * Flexible parsing options
  * Reliable InnerTube API-based fetching

### Data Extraction (ytapi)

* **Channel Information**
  * Comprehensive channel metadata
  * Subscriber count, views, and engagement metrics
  * Avatar and banner image URLs
  * Social media links and about information

* **Video Intelligence**
  * Detailed video metadata retrieval
  * Thumbnail extraction in multiple resolutions
  * Live stream and shorts detection
  * Related videos and chapters extraction
  * Embed code generation

* **Search & Discovery**
  * Advanced search capabilities (videos, channels, playlists)
  * Trending videos across categories
  * Shorts and live stream search
  * Playlist content extraction
  * No official API dependency

* **Captions & Transcripts**
  * Available language detection
  * Timed transcript retrieval
  * Transcript search functionality
  * Plain text transcript extraction

## 🚀 Installation

```bash
pip install -U llm4free
```

## 💻 Quick Start Guide

### Video Downloading

```python
from llm4free import Handler

# Basic video download
downloader = Handler('https://youtube.com/watch?v=dQw4w9WgXcQ')
downloader.save()

# Advanced download with custom settings
downloader = Handler(
    query='python tutorial',  # Search query
    format='mp4',            # Format (mp4, mp3)
    quality='720p',          # Quality (144p to 4K)
    limit=5                  # Number of videos to download
)
downloader.auto_save(dir='./downloads')
```

### Transcript Extraction

```python
from llm4free import YTTranscriber

# Get video transcript (uses InnerTube API for reliability)
transcript = YTTranscriber.get_transcript('https://youtube.com/watch?v=dQw4w9WgXcQ')

# Each entry has: text, start time, duration
for entry in transcript[:5]:
    print(f"[{entry['start']:.1f}s] {entry['text']}")

# Get transcript in a specific language
spanish_transcript = YTTranscriber.get_transcript(
    'dQw4w9WgXcQ',  # Video ID or URL
    languages='es'   # Language code
)

# Get any available transcript (when language doesn't matter)
any_transcript = YTTranscriber.get_transcript(
    'dQw4w9WgXcQ',
    languages=None  # Get first available
)
```

### Channel Information

```python
from llm4free import Channel

# Create a channel instance
channel = Channel('@PewDiePie')  # Handle, ID, or URL

# Access channel metadata
print(f"Channel: {channel.name}")
print(f"Subscribers: {channel.subscribers}")
print(f"Total Views: {channel.views}")
print(f"Country: {channel.country}")

# Get media URLs
print(f"Avatar: {channel.avatar}")
print(f"Banner: {channel.banner}")

# Get recent uploads
recent_videos = channel.uploads(10)  # 10 most recent videos
```

### Video Metadata

```python
from llm4free import Video

# Get video information
video = Video('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
metadata = video.metadata

print(f"Title: {metadata['title']}")
print(f"Views: {metadata['views']}")
print(f"Duration: {metadata['duration']} seconds")
print(f"Upload Date: {metadata['upload_date']}")

# New properties
print(f"Is Live: {video.is_live}")
print(f"Is Short: {video.is_short}")
print(f"Hashtags: {video.hashtags}")

# Get related videos
related = video.get_related_videos(5)

# Get video chapters
chapters = video.get_chapters()

# Get thumbnails
thumbnails = video.thumbnail_urls
print(f"Default thumbnail: {thumbnails['default']}")
print(f"High quality: {thumbnails['high']}")
```

### Search & Trending

```python
from llm4free import Search, Extras

# Search for videos
video_results = Search.videos("Python tutorial", limit=5)

# Search for channels
channel_results = Search.channels("coding", limit=3)

# Search for shorts
shorts = Search.shorts("funny cats", limit=5)

# Search for live streams
live = Search.live_streams("gaming", limit=5)

# Get trending videos
trending = Extras.trending_videos(limit=10)

# Get category-specific videos
music_videos = Extras.music_videos(limit=5)
gaming_videos = Extras.gaming_videos(limit=5)
shorts_videos = Extras.shorts_videos(limit=5)
```

### Captions API

```python
from llm4free.Extra.YTToolkit.ytapi import Captions

# Get available caption languages
languages = Captions.get_available_languages('dQw4w9WgXcQ')
for lang in languages:
    print(f"{lang['code']}: {lang['name']} (auto: {lang['is_auto']})")

# Get timed transcript
transcript = Captions.get_timed_transcript('dQw4w9WgXcQ', language='en')
for entry in transcript[:3]:
    print(f"[{entry['start']:.1f}s] {entry['text']}")

# Get plain text transcript
text = Captions.get_transcript('dQw4w9WgXcQ')
print(text[:200])

# Search within transcript
results = Captions.search_transcript('dQw4w9WgXcQ', 'never gonna')
for r in results:
    print(f"{r['start']:.1f}s: {r['text']}")
```

## 📓 Detailed Documentation

<details>
<summary><strong>Video Downloader (Handler)</strong></summary>

The `Handler` class provides powerful video downloading capabilities:

```python
from llm4free import Handler

# Initialize with video URL or search query
downloader = Handler('https://youtube.com/watch?v=dQw4w9WgXcQ')

# Basic download with default settings
downloader.save()  # Saves to current directory

# Download with custom settings
downloader.save(
    filename='custom_name',  # Custom filename
    format='mp3',           # Format (mp4, mp3)
    quality='highest',      # Quality setting
    output_path='./videos'  # Output directory
)

# Batch download from search
batch_downloader = Handler(
    query='python tutorials',
    limit=5,                # Number of videos
    format='mp4',
    quality='720p'
)
batch_downloader.auto_save()

# Get download progress
progress = downloader.progress
print(f"Download progress: {progress}%")

# Get download history
history = downloader.history
print(f"Downloaded files: {history}")
```
</details>

<details>
<summary><strong>Transcript Retriever (YTTranscriber)</strong></summary>

The `YTTranscriber` class extracts video transcripts using YouTube's InnerTube API:

```python
from llm4free import YTTranscriber

# Get transcript with timestamps
transcript = YTTranscriber.get_transcript('dQw4w9WgXcQ')
for entry in transcript:
    print(f"[{entry['start']:.2f}s] {entry['text']}")

# Get transcript in specific language
spanish = YTTranscriber.get_transcript('dQw4w9WgXcQ', languages='es')

# Get any available transcript
any_lang = YTTranscriber.get_transcript('dQw4w9WgXcQ', languages=None)

# Use with proxies
transcript = YTTranscriber.get_transcript(
    'dQw4w9WgXcQ',
    proxies={'http': 'http://proxy:8080'}
)
```
</details>

<details>
<summary><strong>Channel Class</strong></summary>

The `Channel` class provides comprehensive access to YouTube channel data:

```python
from llm4free import Channel

# Initialize with channel handle, ID, or URL
channel = Channel('@PewDiePie')

# Basic information
print(f"Name: {channel.name}")
print(f"ID: {channel.id}")
print(f"Subscribers: {channel.subscribers}")
print(f"Total Views: {channel.views}")
print(f"Country: {channel.country}")

# Media URLs
print(f"Avatar: {channel.avatar}")
print(f"Banner: {channel.banner}")
print(f"URL: {channel.url}")

# Content
print(f"Description: {channel.description}")
print(f"Social Links: {channel.socials}")

# Live status
if channel.live:
    print(f"Currently streaming: {channel.streaming_now}")

# Get videos
recent_uploads = channel.uploads(20)  # Get 20 most recent videos
```
</details>

<details>
<summary><strong>Video Class</strong></summary>

The `Video` class extracts detailed information about YouTube videos:

```python
from llm4free import Video

# Initialize with video ID or URL
video = Video('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

# Get comprehensive metadata
metadata = video.metadata
print(f"Title: {metadata['title']}")
print(f"Views: {metadata['views']}")
print(f"Duration: {metadata['duration']} seconds")
print(f"Upload Date: {metadata['upload_date']}")

# New properties
print(f"Is Live: {video.is_live}")
print(f"Is Short: {video.is_short}")
print(f"Hashtags: {video.hashtags}")

# Get related videos
related = video.get_related_videos(5)

# Get chapters (if available)
chapters = video.get_chapters()
if chapters:
    for ch in chapters:
        print(f"{ch['start_time']}: {ch['title']}")

# Stream comments (from initial page load)
for comment in video.stream_comments(limit=10):
    print(f"{comment['author']}: {comment['text']}")

# Get thumbnails in different resolutions
thumbnails = video.thumbnail_urls
print(f"Default thumbnail: {thumbnails['default']}")
print(f"High quality thumbnail: {thumbnails['high']}")
print(f"Maximum resolution thumbnail: {thumbnails['maxres']}")

# Get embed code and URL
print(f"Embed HTML: {video.embed_html}")
print(f"Embed URL: {video.embed_url}")
```
</details>

<details>
<summary><strong>Search & Extras Classes</strong></summary>

The `Search` and `Extras` classes provide discovery capabilities:

```python
from llm4free import Search, Extras

# Search for videos with advanced options
video_results = Search.videos("Python tutorial", limit=5)

# Search for channels
channel_results = Search.channels("coding", limit=3)

# Search for playlists
playlist_results = Search.playlists("music mix", limit=3)

# New search methods
shorts = Search.shorts("funny", limit=5)
live = Search.live_streams("gaming", limit=5)
long_videos = Search.videos_by_duration("tutorial", duration="long")
recent = Search.videos_by_upload_date("news", upload_date="today")

# Get trending videos by region
trending = Extras.trending_videos(limit=10, region="US")

# Get category-specific videos
music = Extras.music_videos(limit=5)
gaming = Extras.gaming_videos(limit=5)
shorts = Extras.shorts_videos(limit=5)
movies = Extras.movies(limit=5)
podcasts = Extras.podcasts(limit=5)
```
</details>

## 📚 Module Structure

| Module | File | Description |
|--------|------|-------------|
| **Video Downloader** | [`YTdownloader.py`](YTdownloader.py) | YouTube video downloading with format and quality options |
| **Transcript Retriever** | [`transcriber.py`](transcriber.py) | InnerTube API-based transcript extraction |
| **Channel Data** | [`ytapi/channel.py`](ytapi/channel.py) | Channel metadata and interaction |
| **Video Information** | [`ytapi/video.py`](ytapi/video.py) | Video information extraction |
| **Search** | [`ytapi/query.py`](ytapi/query.py) | Advanced search capabilities |
| **Trending** | [`ytapi/extras.py`](ytapi/extras.py) | Trending and category-based video retrieval |
| **Playlists** | [`ytapi/playlist.py`](ytapi/playlist.py) | Playlist metadata extraction |
| **Captions** | [`ytapi/captions.py`](ytapi/captions.py) | Caption/transcript extraction wrapper |
| **Suggestions** | [`ytapi/suggestions.py`](ytapi/suggestions.py) | Search autocomplete and trending searches |
| **Shorts** | [`ytapi/shorts.py`](ytapi/shorts.py) | YouTube Shorts functionality |
| **Hashtags** | [`ytapi/hashtag.py`](ytapi/hashtag.py) | Hashtag-related video discovery |

## ⚠️ Disclaimer

> [!WARNING]
> This toolkit is designed for educational and research purposes only. Please use responsibly and in accordance with YouTube's terms of service. The developers are not responsible for any misuse of this software.

> [!IMPORTANT]
> Web scraping is inherently fragile. YouTube may change their website structure or API at any time, which could break functionality. If you encounter issues, please report them on GitHub.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

<div align="center">
  <p>
    <a href="https://t.me/PyscoutAI"><img alt="Telegram Group" src="https://img.shields.io/badge/Telegram%20Group-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
    <a href="https://youtube.com/@OEvortex"><img alt="YouTube" src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white"></a>
    <a href="https://buymeacoffee.com/oevortex"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>
  </p>
</div>
