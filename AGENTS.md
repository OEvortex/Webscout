# Webscout - QWEN Context File

## Project Overview

**Webscout** is a comprehensive Python toolkit for web search, AI interaction, and digital utilities. It provides unified access to 90+ AI providers, multiple search engines, text-to-image/speech generation, developer tools, and an OpenAI-compatible API server — all through a single library.

**Key Characteristics:**
- **Package Name:** `webscout` (PyPI)
- **Python Version:** >=3.10
- **License:** Apache-2.0
- **Repository:** https://github.com/OEvortex/Webscout
- **Author:** OEvortex (koulabhay26@gmail.com)

## Architecture

The project is organized into several key layers:

```
webscout/
├── Provider/          # AI provider implementations (63+ providers)
│   ├── Openai_comp/   # OpenAI-compatible provider versions
│   ├── TTI/           # Text-to-Image providers
│   ├── TTS/           # Text-to-Speech providers
│   ├── STT/           # Speech-to-Text providers
│   ├── AISEARCH/      # AI-powered search providers
│   └── UNFINISHED/    # Experimental providers
├── search/            # Multi-engine web search (DuckDuckGo, Bing, Brave, etc.)
├── server/            # OpenAI-compatible FastAPI server
├── swiftcli/          # CLI framework
├── scout/             # HTML parser and web crawler
├── litagent/          # User-agent rotation and IP toolkit
├── zeroart/           # ASCII art generator
├── Extra/             # Additional utilities
├── AIbase.py          # Base class for provider implementations
├── AIauto.py          # Auto-failover logic
├── client.py          # Unified Python client
├── models.py          # Model registry (LLM, TTS, TTI)
├── prompt_manager.py  # System prompt management
├── sanitize.py        # Stream sanitization
└── cli.py             # Command-line interface entry point
```

## Building and Running

### Dependency Management (Use `uv` Only)

This project uses `uv` for all Python environment management. **Never run bare `python` or `pip` directly.**

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Run with extra dependencies
uv run --extra api webscout-server
uv run --extra dev pytest
```

### CLI Usage

```bash
# Show help
uv run webscout --help

# Search the web
uv run webscout text -k "python programming"
uv run webscout text -k "climate change" -e bing
uv run webscout images -k "mountains"
uv run webscout news -k "AI breakthrough" -t w

# Weather info
uv run webscout weather -l "New York"

# Translation
uv run webscout translate -k "Hola" --to en

# Show version
uv run webscout version
```

### API Server

```bash
# Start the OpenAI-compatible API server
uv run --extra api webscout-server
uv run --extra api webscout-server --port 8080 --host 0.0.0.0 --debug
```

### Docker

```bash
# Build and run
docker-compose up webscout-api

# No-auth profile
docker-compose -f docker-compose.yml -f docker-compose.no-auth.yml up webscout-api
```

### Testing

```bash
# Run tests
uv run pytest

# Run specific test markers
uv run pytest -m "not live"  # Skip network-dependent tests
```

### Linting and Formatting

```bash
# Lint with ruff
uv run ruff check .

# Format with ruff
uv run ruff format .
```

## Development Conventions

### Code Style
- **Line length:** 100 characters (configured in `pyproject.toml`)
- **Target Python:** 3.9+ (runtime requires 3.10+)
- **Linting rules:** E, F, W, I (with E501, F403, F401 ignored)
- **Formatter:** ruff

### Provider Development
When adding new providers:
1. Subclass `Provider` from `webscout.AIbase`
2. Implement: `ask(prompt, ...)`, `chat(prompt, ...)`, `get_message(response)`
3. Use consistent CamelCase class names matching filenames
4. Add static import in `webscout/Provider/__init__.py`
5. Prefer `requests.Session` for HTTP clients
6. Avoid global mutable state
7. Add tests under `tests/providers/`
8. Update `Provider.md` documentation

### Testing Practices
- Tests live in `tests/` directory
- Network-dependent tests use `@pytest.mark.live` marker
- **NO MOCKS OR FAKE RESPONSES** — Never use mocks, stubs, or fabricated responses in tests. Always use real clients and actual API calls to catch production-level bugs. The goal is to find real-world issues before they reach users.
- Test both normal and error behavior including streaming
- Use real HTTP requests against actual provider endpoints
- Validate real response structures, not hardcoded fake data

### Import Conventions
- Main package (`webscout/__init__.py`) uses wildcard imports with `# noqa: F403`
- Client is explicitly imported: `from .client import Client`
- Model registry exposed as: `from .models import model`

## Key Dependencies

### Core
- `curl_cffi` - HTTP client with browser impersonation
- `aiohttp` - Async HTTP
- `rich` - Rich terminal output
- `pydantic` - Data validation
- `lxml` - HTML/XML parsing
- `cloudscraper` - Cloudflare bypass
- `browser-cookie3` - Browser cookie extraction

### Optional
- **api:** `fastapi`, `uvicorn`, `websockets`, `tiktoken`, `jinja2`
- **dev:** `ruff`, `pytest`

## Entry Points

| Command | Module |
|---------|--------|
| `webscout` / `WEBS` | `webscout.cli:main` |
| `webscout-server` / `webscout-serve` | `webscout.server.server:main` |

## Documentation

Comprehensive documentation is in `docs/`:
- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [CLI Reference](docs/cli.md)
- [Python Client](docs/client.md)
- [API Server](docs/openai-api-server.md)
- [Model Registry](docs/models.md)
- [Tool Calling](docs/tool-calling.md)
- [Search Docs](docs/search.md)
- [Provider Development](docs/provider-development.md)
- [Deployment](docs/deployment.md)
- [Docker](docs/DOCKER.md)
- [Troubleshooting](docs/troubleshooting.md)

## Provider Matrix

- **63 total AI providers** supported
- **37 providers** have both normal and OpenAI-compatible implementations
- **17 providers** have only normal implementations
- **5 providers** have only OpenAI-compatible implementations
- TTI, TTS, and STT providers in dedicated subdirectories

See [Provider.md](Provider.md) for the complete matrix.
