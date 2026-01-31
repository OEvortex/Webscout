# Webscout Documentation Hub
> Last updated: 2025-12-20  
> Maintained by [Webscout](https://github.com/OEvortex/Webscout)

Welcome to the central entry point for everything you need to know about Webscout. This hub is organized around the actual modules that live inside the repository so you can quickly jump from high-level concepts to concrete implementation details.

## 📚 **[Complete Documentation Index →](DOCUMENTATION_INDEX.md)**
*Navigate all docs, find learning paths, search by use case, and get started quickly!*

---

## 🔗 Quick Navigation

| Topic | Why it matters | Primary Reference |
|-------|----------------|-------------------|
| Overall architecture | Understand how CLI, server, client, providers, and extras fit together | [docs/architecture.md](architecture.md) |
| Command line tooling | Detailed reference for every `webscout` CLI command and option | [docs/cli.md](cli.md) |
| Unified Python client | Auto-failover chat & image client backed by `webscout/client.py` | [docs/client.md](client.md) |
| Model registry | Enumerate LLM, TTS, and TTI models exposed via `webscout/models.py` | [docs/models.md](models.md) |
| OpenAI-compatible API server | Deploy FastAPI server that proxies any Webscout provider | [docs/openai-api-server.md](openai-api-server.md) |
| Search stack | DuckDuckGo/Yep/Bing/Yahoo engines + CLI usage | [docs/search.md](search.md) |
| HTML parser & crawler | Deep dive into `webscout/scout` | [docs/scout.md](scout.md) |
| Stream sanitizers | Advanced SSE/HTTP stream processing utilities | [docs/sanitize.md](sanitize.md) |
| Decorators & utilities | Retry/timing helpers from `webscout/AIutel.py` | [docs/decorators.md](decorators.md) |
| Docker & deployment | Images, compose profiles, env vars | [docs/DOCKER.md](DOCKER.md) |
| GGUF tooling | Model conversion helpers (`webscout/Extra/gguf.py`) | [docs/gguf.md](gguf.md) |
| Inferno local LLMs | Run local servers compatible with Webscout providers | [docs/inferno.md](inferno.md) |
| LitPrinter | Debug printing companion shipped with Webscout | [docs/litprinter.md](litprinter.md) |
| LitAgent | Advanced User Agent & IP rotation toolkit | [docs/litagent.md](litagent.md) |
| Weather toolkit | Weather + ASCII weather helpers inside `webscout/Extra` | [docs/weather.md](weather.md) |
| ZeroArt ASCII generator | Zero-dependency ASCII art text generator with multiple fonts and effects | [docs/zeroart.md](zeroart.md) |
| Provider matrix | Complete list of providers and locations | [Provider.md](../Provider.md) |

## 🧭 How to Use This Hub

1. **Start with the architecture overview** if you are new to the codebase or planning a big change. It explains the flow between public interfaces, search engines, providers, and helper modules.
2. **Jump into topic-specific guides** (CLI, client, server, search, etc.) once you know which layer you want to extend.
3. **Reference module-level docs** (decorators, sanitizer, scout, GGUF, etc.) for implementation details or API signatures.
4. **Use the provider matrix** whenever you need to locate a provider implementation quickly.

## 🗂️ Project Map at a Glance

- `webscout/cli.py` – Rich CLI built on `swiftcli` with commands for DuckDuckGo, Yep, Bing, Yahoo, and weather utilities.
- `webscout/client.py` – Unified chat + image client with intelligent provider/model resolution and automatic failover.
- `webscout/server/` – FastAPI-based OpenAI-compatible server (`docs/openai-api-server.md` covers routes, config, env vars).
- `webscout/search/` – Shared search abstractions (DuckDuckGo, Yep, Bing, Yahoo) plus result formatting helpers.
- `webscout/Provider/` – Provider implementations (normal + OpenAI-compatible) including AI search, TTI, TTS, STT, and experiments.
- `webscout/Extra/` – Auxiliary toolkits like GGUF conversion, weather clients, temp mail, Git/YouTube utilities.
- `docs/` – This folder: each guide is sourced directly from the modules above so it stays true to the code.

## 🆕 Recently Added Docs

- **Architecture Overview** — visual + textual description of the runtime layers.
- **CLI Reference** — exhaustive explanation of `webscout` command families.
- **Unified Client Guide** — how to leverage the `Client` failover logic from Python code.
- **Model Registry Guide** — using `model.llm`, `model.tts`, and `model.tti` helpers.

## 🙌 Contributing to Documentation

- When you add a feature, update or append the relevant topic in this hub so future contributors can find it.
- If you introduce a brand new area (e.g., a new toolkit under `webscout/Extra`), create a dedicated doc and list it in the table above.
- Keep examples synchronized with the code (import paths, parameter names, defaults, and behaviors should match the actual modules).

Need something that is not documented yet? Open an issue or PR and link back to this hub so we can keep the map current.
