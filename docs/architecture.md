# LLM4Free Architecture Overview
> Last updated: 2025-12-20  
> Relates to: `llm4free/cli.py`, `llm4free/client.py`, `llm4free/server/`, `llm4free/search/`, `llm4free/Provider/`, `llm4free/Extra/`

LLM4Free bundles multiple user-facing entry points (CLI, Python client, and an OpenAI-compatible API server) on top of a shared set of engines, providers, and utilities. This document maps how these layers interact so you can reason about changes confidently.

## 🧱 Layered View

```mermaid
flowchart TD
    subgraph EntryPoints
        CLI[CLI (llm4free/cli.py)]
        Client[Python Client (llm4free/client.py)]
        Server[OpenAI-Compatible Server (llm4free/server)]
    end

    subgraph Core
        Search[Search Engines (llm4free/search)]
        Providers[Providers (llm4free/Provider)]
        Extras[Extras & Toolkits (llm4free/Extra)]
        Utilities[Utilities (sanitize.py, AIutel.py, etc.)]
        Models[Model Registry (llm4free/models.py)]
    end

    CLI --> Search
    CLI --> Providers
    Client --> Providers
    Client --> Extras
    Client --> Models
    Server --> Providers
    Server --> Utilities
    Search --> Providers
    Extras --> Providers
```

- **Entry Points** convert user intent (commands/API calls) into provider requests.
- **Core Modules** encapsulate the heavy lifting: crawling websites, calling remote LLMs, handling audio/image generation, sanitizing streams, and enumerating models.

## 🔌 Entry Points

### Command Line Interface (`llm4free/cli.py`)
- Built on `swiftcli` with separate command groups for DuckDuckGo, Yep, Bing, Yahoo, and weather utilities.
- Uses `_print_data` / `_print_weather` helpers to keep terminal output consistent.
- Relies on the same search/provider classes exported in `llm4free/__init__.py`, so CLI behavior matches the Python API.

### Unified Python Client (`llm4free/client.py`)
- Provides auto-failover chat and image APIs through `Client.chat.completions.create()` and `Client.images.generate()`.
- Dynamically discovers OpenAI-compatible providers (`llm4free/Provider/OPENAI`) and TTI providers, caches instances, and performs fuzzy model resolution.
- Shares provider cache with the server, so runtime cost of imports stays low.

### OpenAI-Compatible Server (`llm4free/server/`)
- FastAPI app that exposes `/v1/*` routes mirroring OpenAI's schema.
- Uses `providers.py` to map model names like `ProviderName/model-id` back to actual provider classes.
- Pulls configuration from `config.py` plus environment variables documented in `docs/openai-api-server.md` and `docs/DOCKER.md`.

## 🔍 Core Modules

### Search Stack (`llm4free/search/`)
- Houses protocol-specific engines (See `llm4free/search/engines/*`) plus shared HTTP client and result serializers.
- DuckDuckGo/Yep/Bing/Yahoo commands import from here, so adding new CLI options usually starts with an engine update.

### Providers (`llm4free/Provider/`)
- Normal providers live alongside OpenAI-compatible wrappers (`llm4free/Provider/OPENAI`).
- Specialty directories: `AISEARCH`, `TTI`, `TTS`, `STT`, `UNFINISHED`.
- The matrix in `Provider.md` maps every provider to its implementation file.

### Extras (`llm4free/Extra/`)
- Optional toolkits packaged with LLM4Free (GGUF converter, weather clients, temp mail, YT toolkit, Git API helper, etc.).
- Exported through `llm4free/Extra/__init__.py` so they become part of the public API when you `import llm4free`.

### Utilities
- `llm4free/sanitize.py` – SSE/stream sanitization for server + client streaming paths.
- `llm4free/AIutel.py` – Decorators for retry/timing (documented in `docs/decorators.md`).
- `llm4free/update_checker.py` – Optional PyPI update notifier executed in `llm4free/__init__.py`.

### Models Registry (`llm4free/models.py`)
- Enumerates LLM, TTS, and TTI models exposed by providers.
- Used by documentation examples (README, docs/models.md) and can power custom tooling (e.g., provider dashboards).

## 🔄 Typical Data Flows

1. **CLI ➜ Search Engine ➜ Provider**
   - `llm4free images -k "python"` → `DuckDuckGoSearch.images()` (HTTP scraping) → results printed via `_print_data`.
2. **Client ➜ Provider Failover**
   - `Client().chat.completions.create(model="gpt-4o")` → resolves provider & model → tries preferred provider → falls back through fuzzily-matched providers if necessary.
3. **Server ➜ Provider ➜ sanitize_stream**
   - `/v1/chat/completions` request hits FastAPI → provider resolved → streaming responses run through `sanitize_stream()` before being sent to clients.
4. **Extras ➜ Providers**
   - GGUF converter uses huggingface + llama.cpp builders and is fully independent, but still exported to users alongside the main modules.

## 🧩 When Adding New Functionality

| Task | Touch Points |
|------|--------------|
| Add a CLI command | `llm4free/cli.py` + corresponding engine/provider + update `docs/cli.md` |
| Add a provider | Implement in `llm4free/Provider/` (and optionally `OPENAI/`), update `Provider.md`, consider `models.py` exposure |
| Add server capability | Update `llm4free/server/*`, document in `docs/openai-api-server.md`, ensure CLI/Client can hit the new route if needed |
| Extend Extras | Implement under `llm4free/Extra/`, export in `__init__.py`, add documentation entry under `docs/README.md` |
| Add new registry info | Update `llm4free/models.py` or referencing docs (`docs/models.md`) |

## 🧪 Testing & Debugging Hooks

- CLI commands can be run locally with `uv run llm4free ...` to ensure option parsing remains correct.
- Client failover prints last provider when `print_provider_info=True` – useful when debugging provider availability.
- The server exposes `/health` (see Docker docs) to monitor deployments.
- `sanitize_stream` and decorators have dedicated docs you can reference when debugging streaming issues or retries.

## 📚 Related Documents

- [docs/cli.md](cli.md) – exhaustive CLI reference.
- [docs/client.md](client.md) – deep dive into the unified client.
- [docs/models.md](models.md) – using the model registry helpers.
- [docs/openai-api-server.md](openai-api-server.md) – server configuration & endpoints.
- [Provider.md](../Provider.md) – provider matrix you can cross-reference while navigating the codebase.
