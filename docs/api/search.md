# Search API Reference

## Search Engines

LLM4Free provides a unified search interface supporting multiple search engines.

### Available Engines

| Engine | Category | Features |
|--------|----------|----------|
| DuckDuckGo | Text, News, Images, Videos | Default engine, privacy-focused |
| Bing | Text, News, Suggestions | Microsoft search |
| Brave | Text, News, Images | Privacy-focused |
| Yahoo | Text, News, Videos | Classic search |
| Wikipedia | Text | Encyclopedia |
| Mojeek | Text | Independent search |

### Using Search Engines

```python
from llm4free.search import DuckDuckGoSearch

searcher = DuckDuckGoSearch()
results = searcher.run(keywords="Python programming", max_results=10)

for result in results:
    print(result.title, result.url)
```

### Server API

Search is also available via the API server:

```bash
# Text search
curl "http://localhost:8000/search?q=Python+tutorials&engine=duckduckgo"

# News search
curl "http://localhost:8000/search?q=AI+news&type=news"

# Get available engines
curl "http://localhost:8000/search/provider"
```

### Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `engine` | string | Search engine name |
| `max_results` | int | Maximum results (default: 10) |
| `region` | string | Region code |
| `safesearch` | string | Safe search: on, moderate, off |
| `type` | string | Search type: text, news, images, videos |

## CLI Usage

```bash
# Basic search
llm4free ddg "Python tutorials"

# Search with specific engine
llm4free search "AI news" --engine brave
```
