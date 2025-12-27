# Webscout - Copilot / AI Agent Instructions

Purpose: concise, actionable guidance so an AI coding agent can be productive immediately when editing Webscout.

1) Big picture (what changes touch where)
- webscout/ is the package root. Major subsystems:
  - webscout/Provider/ : Many AI provider implementations. Two important flavors:
    - webscout/Provider/OPENAI/ : OpenAI-compatible wrappers (preferred for API server discovery).
    - webscout/Provider/TTI/ : Text-to-Image providers.
  - webscout/search/ : Search engine backends (DuckDuckGo, Bing, Yahoo, Yep, etc.).
  - webscout/server/ : FastAPI-based OpenAI-compatible API server (routes, provider discovery, request handling).
  - webscout/cli.py & webscout/swiftcli/ : CLI entrypoints and helpers.
  - webscout/Extra/ : Misc utilities (gguf, YTToolkit, tempmail, etc.).
  - docs/ : Human-facing docs (use as canonical examples & copy for README updates).

2) Key developer workflows (commands you can run)
- Use uv for all commands: We use uv to manage the Python environment and run tools. Never run bare `python` or `pip` directly — always run commands with `uv` to avoid environment drift and to use the project's lockfile. Examples and useful commands:
  - `uv pip install <package>` / `uv pip uninstall <package>` — manage dependencies
  - `uv sync` — install dependencies declared in pyproject.toml and uv.lock (preferred for reproducible environments)
  - `uv run <command>` — run a script or tool inside the uv environment (e.g., `uv run pytest`, `uv run webscout`)
  - `uv run --extra api webscout-server` — run the API server with extra dependencies
- Install dev deps: `pip install -e "[dev,api]"` (or prefer `uv sync --extra dev --extra api` when using uv).
- Run CLI locally: `uv run webscout` (you can also use `python -m webscout` when necessary, but prefer `uv run`).
- Start API server (dev): `uv run --extra api webscout-server -- --debug` or `webscout-server --debug`.
  - The server prints provider summaries and exposes docs at `http://localhost:8000/docs` by default.
- Release pipeline: publishing is automated by .github/workflows/publish-to-pypi.yml and release-with-changelog.yml; version bumps are date-based in webscout/version.py and performed by the workflow.
- Linting & formatting: Ruff settings are in pyproject.toml (line-length = 100). Run `uv run ruff .` or `ruff .` to check.
- Tests: pytest is a dev dependency; run tests with `uv run pytest` to ensure they use the project's environment.

3) Project-specific conventions and patterns (essential)
- Provider discovery (server/providers.py): OpenAI-compatible providers are discovered by importing webscout.Provider.OPENAI and inspecting classes that subclass OpenAICompatibleProvider.
  - Important: For a provider to be auto-registered it must:
    - Live under webscout/Provider/OPENAI/ and be imported in webscout/Provider/OPENAI/__init__.py (static imports are used).
    - Subclass OpenAICompatibleProvider (see webscout/Provider/OPENAI/base.py).
    - HAVE a `required_auth` attribute set and be explicitly marked `required_auth = False` if it should be included in the public provider_map without user API keys; discovery code only includes classes where `hasattr(obj, 'required_auth') and not getattr(obj, 'required_auth', True)`.
    - Optionally define `AVAILABLE_MODELS` (iterable) to register model-specific keys in the provider map (e.g., `MyProvider/fast-model`).
  - Example (minimal provider skeleton):

```py
# webscout/Provider/OPENAI/myprovider.py
from webscout.Provider.OPENAI.base import OpenAICompatibleProvider

class MyProvider(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["fast", "accurate"]

    @property
    def models(self):
        return type("M", (), {"list": lambda self: ["fast", "accurate"]})()

    def chat(self):
        ... implement provider chat completions ...
```

- When adding an OpenAI-compatible provider, add an import line in webscout/Provider/OPENAI/__init__.py so the class gets discovered.

- Normal providers (webscout/Provider/): Normal providers are the project's canonical provider implementations. When adding a normal provider:
  - Subclass webscout.AIbase.Provider and implement ask(), chat(), and get_message(). See webscout/AIbase.py for the interface and helpful shared attributes (`last_response`, `conversation`).
  - Export the provider via a static import in webscout/Provider/__init__.py so it is available at the package top-level.
  - Use requests.Session for HTTP clients where appropriate and keep provider state minimal so instances are safe to reuse.
  - Add unit tests under tests/providers/ that mock external calls and validate expected behavior (happy path, streaming, and error cases).
  - Add a short usage example to Provider.md and update docs/ where relevant.

- OpenAI-compatible provider expectations: implement .chat/.completions interfaces using the abstract base classes in webscout/Provider/OPENAI/base.py (tools and tool-calls support is available via Tool/ToolDefinition helpers).

- TTI providers: follow similar patterns under webscout/Provider/TTI/ and are discovered via initialize_tti_provider_map (see webscout/server/providers.py).

- Caching: the API server caches provider instances (provider_instances & tti_provider_instances). Providers should be safe to reuse or implement internal state guards if needed.

4) How to add/change CLI commands
- CLI uses swiftcli. Look at webscout/cli.py for patterns: use `@app.command()` and `@option(...)`. Async handlers are supported; swiftcli will run coroutines automatically.
- Keep printed output consistent with rich and Console helpers (`rich.print`, `console.print` patterns already used).

5) Logging & error handling
- Use litprinter.ic for internal diagnostic logs (project uses ic.configureOutput on startup). Use Rich for user-facing console output.
- API server uses FastAPI exceptions (APIError in webscout/server/exceptions.py) and returns OpenAI-compatible error payloads in request_processing.py — follow existing shapes when changing error handling.

6) Release & CI notes (important)
- Publishing to PyPI is automated by .github/workflows/publish-to-pypi.yml. It:
  - Generates a date-based version and updates webscout/version.py
  - Builds a wheel/sdist and publishes using TWINE_PASSWORD (PYPI_API_TOKEN secret)
  - Creates a GitHub release via release-with-changelog.yml using changelog.md or a generated commit list if missing.
- If you modify packaging metadata, update pyproject.toml and ensure package data includes any new files (tool.setuptools.package-data).

7) Tests & PR guidance for AI agents
- If adding behavior, include a small test (pytest) that demonstrates the new API or provider behavior; put tests under tests/ and follow project import patterns (import webscout.<module>). Use CI local style: `pytest -q`.
- When modifying provider behavior, add unit tests that:
  - Validate model registration (AVAILABLE_MODELS mapping)
  - Validate provider discovery (initialize_provider_map / initialize_tti_provider_map)
  - Validate tool-call formatting & tool execution using the Tool helpers in base.py

8) Files & docs you should update when changing features
- docs/ (add or update docs referring to new provider, new CLI commands, or API behavior)
- webscout/Provider/OPENAI/README.md (example usage and model names)
- README.md (top-level quick-start & CLI examples)
- changelog.md (add a short line for user-visible changes so release workflow picks it up)

9) Small guidance Changes
- Keep changes focused and include small usage examples in tests or docs.
- Run `ruff .`  using `uv run ruff` locally; respect `line-length = 100` and the Ruff select/ignore rules in pyproject.toml.
- Run `uvx ty check <file>` to validate type correctness.
- If the change affects runtime (server, CLI), include a short manual-test snippet that a maintainer can run (e.g., `webscout-server --debug` and a sample curl to /v1/chat/completions).

9) Use Modern Python
- Use type annotations liberally; prefer modern syntax
- Always use type hints for function signatures and return types
- each function should have its docstring explaining its purpose, parameters, and return values
- Prefer f-strings for formatting
- Use list/dict/set comprehensions where appropriate

10) Important rules
- Keep changes focused and include small usage examples in tests or docs.
- Run `ruff .`  using `uv run ruff` locally; respect `line-length = 100` and the Ruff select/ignore rules in pyproject.toml.
- Run `uvx ty check <file>` to validate type correctness.
- If the change affects runtime (server, CLI), include a short manual-test snippet that a maintainer can run (e.g., `webscout-server --debug` and a sample curl to /v1/chat/completions).
- Always update files in small batches (manageable chunks)
- Dont add unnecessary comments or redundant code
- Remove unused imports, variables, comments 
- Dont use `python <file>.py` instead of that use `uv run <file>.py`