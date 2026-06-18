# Rename llm4free → llm4free Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the entire `llm4free` Python package to `llm4free` — updating all imports, configs, docs, Docker, and CLI entry points.

**Architecture:** Systematic find-and-replace across all files, then directory rename. Changes are mechanical but high-volume (~2000+ occurrences).

**Tech Stack:** Python, pyproject.toml, Docker, GitHub Actions, MkDocs

---

## Scope Summary

| Category | Files Affected | Key Changes |
|----------|---------------|-------------|
| Python imports | ~150 .py files | `from llm4free` → `from llm4free` |
| Package directory | 1 dir | `llm4free/` → `llm4free/` |
| pyproject.toml | 1 file | name, entry points, coverage, package-data |
| Docker | Dockerfile, 2 compose files | env vars, user, commands |
| Docs | ~40 .md files | references, URLs, examples |
| CI/CD | .github/workflows | version grep paths |
| Tests | tests/*.py | imports, module names |
| Server | llm4free/server/*.py | env vars, strings |

---

### Task 1: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Rename package and entry points**

```toml
[project]
name = "llm4free"
# Using dynamic version from llm4free.version

[project.scripts]
FREE = "llm4free.cli:main"
llm4free = "llm4free.cli:main"
llm4free-server = "llm4free.server.server:main"
llm4free-serve = "llm4free.server.server:main"

[project.urls]
Source = "https://github.com/OEvortex/Webscout"
Tracker = "https://github.com/OEvortex/Webscout/issues"

[tool.coverage.run]
source = ["llm4free"]

[tool.setuptools.packages.find]
include = ["llm4free*"]

[tool.setuptools.dynamic]
version = {attr = "llm4free.version.__version__"}

[tool.setuptools.package-data]
"llm4free" = ["*"]
```

- [ ] **Step 2: Verify**

Run: `grep -n "llm4free" pyproject.toml` — should return 0 matches

---

### Task 2: Rename package directory

**Files:**
- Rename: `llm4free/` → `llm4free/`

- [ ] **Step 1: Rename directory**

```bash
mv llm4free llm4free
```

- [ ] **Step 2: Verify**

Run: `ls llm4free/__init__.py` — should exist  
Run: `ls llm4free/__init__.py` — should fail (not found)

---

### Task 3: Update version.py

**Files:**
- Modify: `llm4free/version.py`

- [ ] **Step 1: Update program name**

```python

__version__ = "2026.6.12"
__prog__ = "llm4free"
```

- [ ] **Step 2: Verify**

Run: `grep "llm4free" llm4free/version.py` — should return 0 matches

---

### Task 4: Bulk find-replace Python imports

**Files:**
- All `.py` files under `llm4free/` and `tests/`

- [ ] **Step 1: Replace all Python imports**

```bash
find llm4free tests -name "*.py" -exec sed -i 's/from llm4free/from llm4free/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/import llm4free/import llm4free/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/"llm4free\./"llm4free./g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.Provider/llm4free.Provider/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.AIbase/llm4free.AIbase/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.AIutel/llm4free.AIutel/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.litagent/llm4free.litagent/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.client/llm4free.client/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.models/llm4free.models/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.server/llm4free.server/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.search/llm4free.search/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.scout/llm4free.scout/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.swiftcli/llm4free.swiftcli/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.Extra/llm4free.Extra/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.zeroart/llm4free.zeroart/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.optimizers/llm4free.optimizers/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.update_checker/llm4free.update_checker/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.cli/llm4free.cli/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.sanitize/llm4free.sanitize/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.model_fetcher/llm4free.model_fetcher/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.version/llm4free.version/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.__main__/llm4free.__main__/g' {} +
find llm4free tests -name "*.py" -exec sed -i 's/llm4free\.__init__/llm4free.__init__/g' {} +
```

- [ ] **Step 2: Catch remaining generic references**

```bash
find llm4free tests -name "*.py" -exec sed -i 's/\bllm4free\b/llm4free/g' {} +
```

- [ ] **Step 3: Verify no remaining imports**

Run: `grep -rn "from llm4free\|import llm4free\|\"llm4free\." llm4free/ tests/` — should return 0 matches

---

### Task 5: Update CLI and server string literals

**Files:**
- Modify: `llm4free/cli.py`
- Modify: `llm4free/server/server.py`
- Modify: `llm4free/server/ui_templates.py` (if exists)

- [ ] **Step 1: Update CLI app name**

In `llm4free/cli.py`, change:
```python
app: CLI = CLI(name="llm4free", help="Search the web with a simple UI", version=__version__)
```

And the version print:
```python
rprint(f"[bold cyan]llm4free version:[/bold cyan] {__version__}")
```

- [ ] **Step 2: Update server strings**

In `llm4free/server/server.py`, replace all `LLM4Free` with `LLM4Free` and `llm4free` with `llm4free` in string literals:
```python
app_title = os.getenv("LLM4FREE_API_TITLE", "LLM4Free API")
app_description = os.getenv(
    "LLM4FREE_API_DESCRIPTION", "OpenAI API compatible interface for various LLM providers"
)
app_version = os.getenv("LLM4FREE_API_VERSION", "0.2.0")
app_docs_url = os.getenv("LLM4FREE_API_DOCS_URL", "/docs")
app_redoc_url = os.getenv("LLM4FREE_API_REDOC_URL", "/redoc")
app_openapi_url = os.getenv("LLM4FREE_API_OPENAPI_URL", "/openapi.json")
```

Update all `LLM4FREECOUT_*` env var references to `LLM4FREE_*`:
```python
default_port = int(os.getenv("LLM4FREE_PORT", os.getenv("PORT", DEFAULT_PORT)))
default_host = os.getenv("LLM4FREE_HOST", DEFAULT_HOST)
default_workers = int(os.getenv("LLM4FREE_WORKERS", "1"))
default_log_level = os.getenv("LLM4FREE_LOG_LEVEL", "info")
default_provider = os.getenv("LLM4FREE_DEFAULT_PROVIDER", os.getenv("DEFAULT_PROVIDER"))
default_base_url = os.getenv("LLM4FREE_BASE_URL", os.getenv("BASE_URL"))
default_debug = os.getenv("LLM4FREE_DEBUG", os.getenv("DEBUG", "false")).lower() == "true"
```

Update print statements:
```python
print("Starting LLM4Free OpenAI API server...")
print("\n=== LLM4Free OpenAI API Server ===")
```

Update uvicorn app strings:
```python
uvicorn_app_str = (
    "llm4free.server.server:create_app_debug" if debug else "llm4free.server.server:create_app"
)
```

- [ ] **Step 3: Verify**

Run: `grep -rn "LLM4FREECOUT_\|LLM4Free\|llm4free" llm4free/server/` — should return 0 matches

---

### Task 6: Update Dockerfile

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Update Dockerfile**

Replace all `llm4free`/`LLM4Free`/`LLM4FREECOUT` references:
- `LLM4FREECOUT_VERSION` → `LLM4FREE_VERSION`
- `LLM4FREECOUT_HOST` → `LLM4FREE_HOST`
- `LLM4FREECOUT_PORT` → `LLM4FREE_PORT`
- `LLM4FREECOUT_WORKERS` → `LLM4FREE_WORKERS`
- `LLM4FREECOUT_LOG_LEVEL` → `LLM4FREE_LOG_LEVEL`
- `LLM4FREECOUT_DEBUG` → `LLM4FREE_DEBUG`
- `LLM4FREECOUT_DATA_DIR` → `LLM4FREE_DATA_DIR`
- `LLM4FREECOUT_REQUEST_LOGGING` → `LLM4FREE_REQUEST_LOGGING`
- `LLM4FREECOUT_API_TITLE` → `LLM4FREE_API_TITLE`
- `LLM4FREECOUT_API_DESCRIPTION` → `LLM4FREE_API_DESCRIPTION`
- `LLM4FREECOUT_API_VERSION` → `LLM4FREE_API_VERSION`
- `LLM4FREECOUT_API_DOCS_URL` → `LLM4FREE_API_DOCS_URL`
- `LLM4FREECOUT_API_REDOC_URL` → `LLM4FREE_API_REDOC_URL`
- `LLM4FREECOUT_API_OPENAPI_URL` → `LLM4FREE_API_OPENAPI_URL`
- `LLM4FREECOUT_CORS_ORIGINS` → `LLM4FREE_CORS_ORIGINS`
- `llm4free-api` → `llm4free-api`
- `llm4free` user → `llm4free` user
- `python -m llm4free.server.server` → `python -m llm4free.server.server`
- `pip install llm4free[api]` → `pip install llm4free[api]`
- Label descriptions: `llm4free-api` → `llm4free-api`
- Comment: `LLM4Free API Server` → `LLM4Free API Server`

- [ ] **Step 2: Verify**

Run: `grep -n "llm4free\|LLM4Free\|LLM4FREECOUT" Dockerfile` — should return 0 matches

---

### Task 7: Update docker-compose files

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.no-auth.yml`

- [ ] **Step 1: Update docker-compose.yml**

Replace all occurrences:
- Service names: `llm4free-api` → `llm4free-api`, `llm4free-api-production` → `llm4free-api-production`, `llm4free-api-dev` → `llm4free-api-dev`, `llm4free-nginx` → `llm4free-nginx`, `llm4free-prometheus` → `llm4free-prometheus`
- Container names: `llm4free-api` → `llm4free-api`, etc.
- Image names: `llm4free-api:latest` → `llm4free-api:latest`, `llm4free-api:dev` → `llm4free-api:dev`
- Volume names: `llm4free-logs` → `llm4free-logs`, `llm4free-data` → `llm4free-data`
- Network name: `llm4free-network` → `llm4free-network`
- All `LLM4FREECOUT_*` env vars → `LLM4FREE_*`
- All `llm4free.` label vars → `llm4free.`
- Python module: `llm4free.server.server` → `llm4free.server.server`
- Comments: `LLM4Free` → `LLM4Free`

- [ ] **Step 2: Update docker-compose.no-auth.yml**

Same pattern — replace all `llm4free`/`LLM4FREECOUT` references.

- [ ] **Step 3: Verify**

Run: `grep -n "llm4free\|LLM4Free\|LLM4FREECOUT" docker-compose.yml docker-compose.no-auth.yml` — should return 0 matches

---

### Task 8: Update __init__.py and __main__.py

**Files:**
- Modify: `llm4free/__init__.py`
- Modify: `llm4free/__main__.py`

- [ ] **Step 1: Update comment in __init__.py**

```python
# llm4free/__init__.py
```

- [ ] **Step 2: Update __main__.py if it references llm4free**

Check and update any string references.

- [ ] **Step 3: Verify**

Run: `grep -n "llm4free" llm4free/__init__.py llm4free/__main__.py` — should return 0 matches

---

### Task 9: Update all documentation files

**Files:**
- All `.md` files in project root and `docs/`

- [ ] **Step 1: Bulk replace in markdown files**

```bash
find . -name "*.md" -not -path "./llm4free/*" -exec sed -i 's/llm4free/llm4free/g' {} +
find . -name "*.md" -not -path "./llm4free/*" -exec sed -i 's/LLM4Free/LLM4Free/g' {} +
find . -name "*.md" -not -path "./llm4free/*" -exec sed -i 's/LLM4FREE/LLM4FREE/g' {} +
```

- [ ] **Step 2: Update mkdocs.yml**

In `mkdocs.yml`:
```yaml
site_name: LLM4Free Documentation
site_url: https://oevortex.github.io/LLM4Free/
repo_name: OEvortex/LLM4Free
repo_url: https://github.com/OEvortex/Webscout
copyright: Copyright &copy; 2024-2026 LLM4Free Contributors
```

Update all navigation links and references.

- [ ] **Step 3: Update AGENTS.md**

Replace all `llm4free`/`LLM4Free`/`LLM4FREE` references with `llm4free`/`LLM4Free`/`FREE`.

- [ ] **Step 4: Verify**

Run: `grep -rn "llm4free\|LLM4Free" --include="*.md" . | grep -v ".github" | head -20` — should be mostly clean

---

### Task 10: Update GitHub workflows

**Files:**
- `.github/workflows/release-with-changelog.yml`

- [ ] **Step 1: Update version grep path**

```yaml
VERSION=$(grep -oP '__version__ = "\K[^"]*' llm4free/version.py)
```

And update pip install reference:
```yaml
echo "pip install --upgrade llm4free==$VERSION" >> RELEASE_NOTES.md
```

- [ ] **Step 2: Verify**

Run: `grep -n "llm4free\|LLM4Free" .github/workflows/*.yml` — should return 0 matches

---

### Task 11: Update ty.toml and any remaining config

**Files:**
- Modify: `ty.toml`

- [ ] **Step 1: Update ty.toml**

```toml
include = [
    "llm4free/Provider/UNFINISHED/**",
]
```

- [ ] **Step 2: Final sweep**

```bash
grep -rn "llm4free\|LLM4Free\|LLM4FREECOUT" --include="*.py" --include="*.toml" --include="*.yml" --include="*.yaml" --include="*.cfg" --include="*.ini" --include="Dockerfile*" . | grep -v ".git/" | head -30
```

---

### Task 12: Run lint and verification

**Files:** (none — verification only)

- [ ] **Step 1: Run ruff check**

Run: `uv run ruff check llm4free/` — should pass with no import errors

- [ ] **Step 2: Run ruff format check**

Run: `uv run ruff format --check llm4free/` — should pass

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/ -x --timeout=30` — should pass (non-live tests)

- [ ] **Step 4: Verify package installs**

Run: `uv sync` — should succeed

- [ ] **Step 5: Verify CLI entry point**

Run: `uv run llm4free --help` — should show help

---

### Task 13: Update remaining provider __init__.py files

**Files:**
- `llm4free/Provider/__init__.py`
- `llm4free/Provider/Openai_comp/__init__.py`
- `llm4free/Provider/AISEARCH/__init__.py`
- `llm4free/Provider/TTS/__init__.py`
- `llm4free/Provider/STT/__init__.py`
- `llm4free/Provider/TTI/__init__.py`

- [ ] **Step 1: Verify imports are updated**

All `from llm4free.Provider...` should now be `from llm4free.Provider...`.

- [ ] **Step 2: Verify**

Run: `grep -rn "llm4free" llm4free/Provider/__init__.py llm4free/Provider/Openai_comp/__init__.py` — should return 0 matches

---

## Self-Review Checklist

1. **Spec coverage:** Every file category (Python, Docker, docs, CI, config) has a dedicated task.
2. **No placeholders:** All steps contain concrete commands and code.
3. **Type consistency:** Env vars use `LLM4FREE_*` everywhere, not mixed with `LLM4FREECOUT_*`.
4. **Verification steps:** Each task includes grep verification.

## Execution Handoff

After saving the plan, determine execution approach via `compose:ask`.
