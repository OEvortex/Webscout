# LLM4Free CLI Reference
> Last updated: 2025-12-20
> Source of truth: [`llm4free/cli.py`](../llm4free/cli.py)

The LLM4Free CLI provides a unified interface for multiple search engines. All commands now support an `--engine` (or `-e`) option to switch between providers, with DuckDuckGo (`ddg`) as the default.

## 🧭 Getting Started

```bash
# List all available commands
llm4free --help

# Show CLI version
llm4free version

# Run a simple search
llm4free text -k "python programming"
```

The CLI uses **Rich** for beautiful, formatted table outputs and informative panels.

## 🔍 Core Commands

| Command | Description | Supported Engines |
|---------|-------------|-------------------|
| `text` | General web search | `ddg`, `bing`, `yahoo`, `brave`, `mojeek`, `wikipedia` |
| `images` | Image search | `ddg`, `bing`, `yahoo` |
| `videos` | Video search | `ddg`, `yahoo` |
| `news` | News search | `ddg`, `bing`, `yahoo` |
| `weather` | Weather information | `ddg`, `yahoo` |
| `answers` | Instant answers | `ddg`, `yahoo` |
| `suggestions`| Query autocomplete | `ddg`, `bing`, `yahoo` |
| `translate` | Text translation | `ddg`, `yahoo` |
| `maps` | POI / Location search | `ddg`, `yahoo` |
| `search` | Shortcut for `text` | Use as a general unified command |

### Common Options

```text
-k, --keywords      (required) Search query or keywords
-e, --engine        Search engine to use (default: ddg)
-m, --max-results   Maximum number of results to display (default: 10)
-r, --region        Region code (e.g., us, uk, wt-wt)
-s, --safesearch    on / moderate / off (default: moderate)
-t, --timelimit     Time filter (d, w, m, y)
```

## 🌦️ Weather & Info

The `weather` command provides a current conditions panel and a 5-day forecast.

```bash
llm4free weather -l "London" -e yahoo
```

## 🧪 Usage Examples

### 1. Multi-Engine Search
```bash
# Default (DuckDuckGo)
llm4free text -k "fastapi tutorial"

# Using Brave Search
llm4free text -k "fastapi tutorial" -e brave

# Using Wikipedia
llm4free text -k "Quantum Physics" -e wikipedia
```

### 2. Media Search
```bash
# Find images on Bing
llm4free images -k "cyberpunk art" -e bing

# Find news on Yahoo
llm4free news -k "space exploration" -e yahoo
```

### 3. Utility Commands
```bash
# Translate text via Yahoo
llm4free translate -k "Hola mundo" --to en -e yahoo

# Get suggestions from DuckDuckGo
llm4free suggestions -q "artificial i" -e ddg
```

## 🛠️ Advanced Options

Certain commands have specific extras:
- **Maps**: `--place` and `--radius` are supported for refinement.
- **Translate**: `--from` (optional) and `--to` (default: `en`).

## 🔗 Related Documentation

- [docs/search.md](search.md) – Technical documentation for the Python Search API.
- [docs/architecture.md](architecture.md) – How the search module is structured.
- [docs/client.md](client.md) – Using the unified `LLM4Free` client.
