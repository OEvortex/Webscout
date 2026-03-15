# Webscout Copilot Instructions

## Purpose

Concise, actionable guidance so an AI coding agent can be productive immediately when editing Webscout.

---

## Agent Orchestration

### Overview

If the subagent tool is available, the main Copilot agent acts strictly as an orchestrator. All research, planning, and heavy reasoning **MUST** be delegated to specialized subagents.

> Note: There may be other subagents available beyond those listed below.

- Always call multiple subagents in parallel.
- Break down tasks into subtasks first.
- For each subtask, call the appropriate subagent or custom agent.

### Available Subagents

#### Reverse
- **Role:** Reverse Engineering & Provider Discovery Agent
- **Responsibilities:**
  - Inspect websites or APIs
  - Extract endpoints, headers, payloads, auth, streaming patterns
  - Generate production-ready Provider classes
- **When to call:**
  - User asks to reverse engineer a website or API
  - User requests a new Provider implementation
  - Unknown or undocumented API behavior
- **Must not:**
  - Modify unrelated files
  - Plan multi-file refactors

#### Plan
- **Role:** Planning & Task Decomposition Agent
- **Responsibilities:**
  - Break large requests into discrete tasks
  - Define execution order
  - Identify required files and agents
- **When to call:**
  - Task spans multiple files
  - Complex refactors or new subsystems
  - Ambiguous or high-level user requests
- **Must not:**
  - Write production code
  - Perform API research

### Agent Calling Rules

- If the subagent tool is available, the main agent **MUST** decide which subagent to call before acting.
- If the subagent tool is available, one or more subagents may be active per task chunk.
- If the subagent tool is available and a task involves multiple concerns, call **Plan** first.
- If the subagent tool is available, never mix reverse engineering, planning, and documentation in one agent.

### Execution Flow

1. Receive user request
2. Classify intent (Reverse / Docstring / Plan)
3. If subagent tool is available, delegate to appropriate subagent
4. If subagent tool is available, receive result
5. Apply or present result

---

## Critical Context Window Management

- ALWAYS work in discrete, focused steps.
- Use **runSubagent** for tasks when the subagent tool is available.
- Break large tasks into smaller chunks.
- Avoid reading large files entirely; search for specific code first using codebase-retrieval.
- Never batch too many operations; use subagents or groups of 3–5 files.

> Always delegate to a subagent rather than risk output truncation.

---

## Code Quality Tools

### Approved
- **Ruff** — `uvx ruff check .` — Linting & formatting
- **Ty** — `uvx ty check .` — Type checking

### Disallowed
- mypy
- pyright
- pylint
- flake8
- black

### Rationale

Ruff is extremely fast and handles linting/formatting. Ty is a modern, faster alternative to mypy/pyright. Multiple tools cause conflicts and slow development.

---

## Project Structure

### Root
- `webscout/`

### Subsystems
- **AI provider implementations** — `webscout/Provider/`
  - **OpenAI-compatible wrappers** — `Openai_comp/`
  - **Text-to-Image providers** — `TTI/`
- **Search engine backends** — `webscout/search/`
- **FastAPI OpenAI-compatible API server** — `webscout/server/`
- **CLI entrypoint** — `webscout/cli.py`
- **CLI helpers** — `webscout/swiftcli/`
- **Misc utilities** — `webscout/Extra/`
- **Human-facing documentation** — `docs/`

---

## Developer Workflows

### Environment
- Always use `uv`; never bare `python` or `pip`.
- Never run one-off Python snippets with `python -c`; instead write test code to a temporary file, run it, then delete the file.

### Common Commands
- `uv pip install <package>`
- `uv pip uninstall <package>`
- `uv run <command>`
- `uv run --extra api webscout-server`
- `uv sync --extra dev --extra api`
- `uv run webscout`
- `uv run --extra api webscout-server -- --debug`
- `uv run pytest`
- `uv run ruff .`

---

## Provider Conventions

### OpenAI-Compatible Providers
#### Discovery
- Must live under `webscout/Provider/OPENAI/`
- Must be imported in `webscout/Provider/OPENAI/__init__.py`
- Must subclass `OpenAICompatibleProvider`
- Must define `required_auth` attribute
- `required_auth` must be `False` to be publicly registered

#### Optional
- Feature: `AVAILABLE_MODELS`

#### Example
```py
class MyProvider(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["fast", "accurate"]

    @property
    def models(self):
        return type("M", (), {"list": lambda self: ["fast", "accurate"]})()

    def chat(self):
        ...
```

### Normal Providers
- Subclass `webscout.AIbase.Provider`
- Implement `ask()`, `chat()`, `get_message()`
- Export via `webscout/Provider/__init__.py`
- Use `requests.Session`
- Add unit tests under `tests/providers/`
- Update `Provider.md` and `docs/`

### TTI Providers
- Follow patterns in `webscout/Provider/TTI/`
- Discovered via `initialize_tti_provider_map`

---

## CLI Conventions

- **Framework:** `swiftcli`
- **Rules:**
  - Use `@app.command()`
  - Use `@option()`
  - Async handlers supported
  - Use `rich` for console output

---

## Logging and Errors

- **Internal:** `litprinter.ic`
- **User-facing:** Rich console

### Server
- Use FastAPI exceptions
- Follow OpenAI-compatible error shapes

---

## Release and CI

- **Versioning:** Date-based in `webscout/version.py`
- **Automation:**
  - `.github/workflows/publish-to-pypi.yml`
  - `release-with-changelog.yml`

---

## Testing Guidelines

- Add tests for new behavior
- Validate provider discovery and model registration
- Use `pytest` under `tests/`

### Structure
- Place unit tests in `tests/providers/` for provider implementations
- Use `unittest.TestCase` for unit tests with `setUp()` methods
- Mock external dependencies using FakeResp or similar patterns
- Test parsing, validation, and error handling
- Name test files as `test_<provider_name>.py`
- Interactive/stress tests use `pytestmark = pytest.mark.skip()` to avoid running in CI
- All test files must pass: `uvx ruff check .` and `uvx ty check .`

---

## Docs To Update

- `docs/`
- `changelog.md`

---

## Modern Python

- Use type annotations
- Add docstrings
- Prefer f-strings
- Use comprehensions

---

# Hard Rules

- **ALWAYS** divide work into small, discrete tasks before acting.
- **If `tool:runSubagent` is available, ALWAYS use it for:**
  - Research or investigation
  - Multi-step planning
  - High-context reasoning
  - Web search or external knowledge gathering
  - Editing or analyzing many files

> If `tool:runSubagent` is not available, skip subagent-only steps entirely.

- **NEVER** perform research, exploration, or large reasoning chains in the main agent. Delegate those to subagents.
- **NEVER** rely on assumptions about the codebase; fetch exact context before reading, modifying, or reasoning about code.
- Batch changes in small groups (3–5 files max). If more are required, split into multiple subagent tasks.
- Respect line-length = 100 and all Ruff rules.
- Remove unused imports, variables, and dead code immediately.
- Never make new unwanted doc files.
- After changes, **ALWAYS** run:
  - `uvx ruff check .`
  - `uvx ty check .`

> Do not proceed until all issues are resolved. Do not use `uvx run`; always use `uv run` instead.
