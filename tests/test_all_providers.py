"""
Webscout provider live tester with per-provider timeouts.

Tests every provider in `llm4free.Provider.__all__` that does not require an
API key, plus optionally auth-required ones if a key is supplied via
--api-key or --api-keys-file.

A 60s hard timeout per provider prevents a single hung endpoint from
blocking the entire run. Each result is categorised as one of:

    WORKING         - chat() returned a non-empty response
    EMPTY           - chat() returned "" / None / no text
    INIT_FAILED     - constructor raised (missing arg, TypeError, etc.)
    RUNTIME_ERROR   - chat() raised (HTTP, parse, auth-on-actually-needed)
    TIMEOUT         - 60s wall-clock exceeded
    SKIPPED_AUTH    - provider required auth and no key was given

Output:
    - pretty live report to stdout
    - machine-readable results to provider_test_results.json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import signal
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

console = Console()
PROVIDER_MODULE_NAME = "llm4free.Provider"


# ──────────────────────────────────────────────────────────────────────
# Timeout helper (POSIX signal.alarm based)
# ──────────────────────────────────────────────────────────────────────

class TimeoutError_(Exception):
    pass


@contextmanager
def wallclock_timeout(seconds: int):
    """Raise TimeoutError_ after `seconds` of wall-clock time.

    Uses SIGALRM, so only works on the main thread under POSIX. This is fine
    because we run providers one at a time on the main thread.
    """
    def _handler(signum, frame):
        raise TimeoutError_(f"timeout after {seconds}s")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ──────────────────────────────────────────────────────────────────────
# Result container
# ──────────────────────────────────────────────────────────────────────

WORKING = "WORKING"
EMPTY = "EMPTY_RESPONSE"
INIT_FAILED = "INIT_FAILED"
RUNTIME_ERROR = "RUNTIME_ERROR"
TIMEOUT = "TIMEOUT"
SKIPPED_AUTH = "SKIPPED_AUTH"


@dataclass
class ProviderResult:
    name: str
    status: str
    auth_required: bool
    error: Optional[str] = None
    error_type: Optional[str] = None
    response_preview: Optional[str] = None
    elapsed_s: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "auth_required": self.auth_required,
            "error": self.error,
            "error_type": self.error_type,
            "response_preview": self.response_preview,
            "elapsed_s": round(self.elapsed_s, 2),
        }


# ──────────────────────────────────────────────────────────────────────
# Core test runner
# ──────────────────────────────────────────────────────────────────────

def _coerce_response(resp: Any) -> str:
    """Best-effort: turn whatever chat() returns into a flat string."""
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        for key in ("text", "content", "message", "delta", "data"):
            if key in resp and isinstance(resp[key], str):
                return resp[key]
        return json.dumps(resp)[:400]
    text_attr = getattr(resp, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    return str(resp)[:400]


def test_one_provider(
    name: str,
    cls: Any,
    api_key: Optional[str],
    prompt: str,
    timeout_s: int,
) -> ProviderResult:
    """Test a single provider and return a categorised result."""
    import time

    auth_required = bool(getattr(cls, "required_auth", False))
    t0 = time.perf_counter()

    # Build init kwargs
    init_kwargs: Dict[str, Any] = {}
    if auth_required:
        if not api_key:
            return ProviderResult(
                name=name,
                status=SKIPPED_AUTH,
                auth_required=True,
                error_type="AuthRequired",
                error="no api key supplied",
            )
        init_kwargs["api_key"] = api_key

    # Instantiate
    try:
        with wallclock_timeout(timeout_s):
            provider = cls(**init_kwargs)
    except TimeoutError_:
        return ProviderResult(
            name=name,
            status=TIMEOUT,
            auth_required=auth_required,
            error_type="Timeout",
            error=f"__init__ exceeded {timeout_s}s",
            elapsed_s=time.perf_counter() - t0,
        )
    except TypeError as e:
        # Missing required constructor arg (e.g. cookie_file) — not the same
        # as a runtime error against the network.
        return ProviderResult(
            name=name,
            status=INIT_FAILED,
            auth_required=auth_required,
            error_type="TypeError",
            error=f"__init__: {e}",
            elapsed_s=time.perf_counter() - t0,
        )
    except Exception as e:
        return ProviderResult(
            name=name,
            status=INIT_FAILED,
            auth_required=auth_required,
            error_type=type(e).__name__,
            error=str(e)[:400],
            elapsed_s=time.perf_counter() - t0,
        )

    # Call chat()
    try:
        with wallclock_timeout(timeout_s):
            response = provider.chat(prompt, stream=False)
    except TimeoutError_:
        return ProviderResult(
            name=name,
            status=TIMEOUT,
            auth_required=auth_required,
            error_type="Timeout",
            error=f"chat() exceeded {timeout_s}s",
            elapsed_s=time.perf_counter() - t0,
        )
    except Exception as e:
        return ProviderResult(
            name=name,
            status=RUNTIME_ERROR,
            auth_required=auth_required,
            error_type=type(e).__name__,
            error=str(e)[:400],
            elapsed_s=time.perf_counter() - t0,
        )

    text = _coerce_response(response).strip()
    elapsed = time.perf_counter() - t0
    if not text:
        return ProviderResult(
            name=name,
            status=EMPTY,
            auth_required=auth_required,
            error_type="EmptyResponse",
            error="chat() returned empty",
            elapsed_s=elapsed,
        )

    return ProviderResult(
        name=name,
        status=WORKING,
        auth_required=auth_required,
        response_preview=text[:160],
        elapsed_s=elapsed,
    )


# ──────────────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────────────

_STATUS_STYLE = {
    WORKING: "green",
    EMPTY: "yellow",
    INIT_FAILED: "red",
    RUNTIME_ERROR: "red",
    TIMEOUT: "red",
    SKIPPED_AUTH: "dim",
}


def render_summary(results: List[ProviderResult]) -> Table:
    table = Table(title="Webscout Provider Test Results", show_lines=False)
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Auth", style="dim")
    table.add_column("Error", style="red", overflow="fold")
    table.add_column("Time", justify="right")

    for r in sorted(results, key=lambda x: (x.status != WORKING, x.name.lower())):
        style = _STATUS_STYLE.get(r.status, "")
        err = r.error or ""
        if r.error_type and r.error and r.status == WORKING:
            err = ""
        table.add_row(
            r.name,
            f"[{style}]{r.status}[/{style}]",
            "yes" if r.auth_required else "no",
            err,
            f"{r.elapsed_s:.1f}s",
        )
    return table


def render_groups(results: List[ProviderResult]) -> None:
    groups: Dict[str, List[ProviderResult]] = {}
    for r in results:
        groups.setdefault(r.status, []).append(r)

    order = [WORKING, EMPTY, RUNTIME_ERROR, INIT_FAILED, TIMEOUT, SKIPPED_AUTH]
    console.print()
    for status in order:
        items = groups.get(status, [])
        if not items:
            continue
        style = _STATUS_STYLE[status]
        names = ", ".join(sorted(r.name for r in items))
        console.print(f"[{style}]{status} ({len(items)}):[/{style}] {names}")


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", help="API key for any auth-required provider")
    parser.add_argument(
        "--api-keys-file",
        type=Path,
        help="JSON file mapping provider name (or 'default') to API key",
    )
    parser.add_argument(
        "--prompt",
        default="Respond with the single word: hello",
        help="Prompt sent to each provider",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Per-provider wall-clock timeout in seconds (default 60)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("provider_test_results.json"),
        help="Where to write the JSON results",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated subset of providers to test",
    )
    parser.add_argument(
        "--include-auth",
        action="store_true",
        help="Also test auth-required providers (requires --api-key or --api-keys-file)",
    )
    args = parser.parse_args()

    # Resolve API keys
    api_keys: Dict[str, str] = {}
    if args.api_key:
        api_keys["default"] = args.api_key
    if args.api_keys_file and args.api_keys_file.exists():
        try:
            api_keys.update(json.loads(args.api_keys_file.read_text()))
        except Exception as e:
            console.print(f"[red]failed to read api-keys-file: {e}[/red]")
            return 1

    default_key = api_keys.get("default")

    # Load module
    provider_mod = importlib.import_module(PROVIDER_MODULE_NAME)
    aibase_mod = importlib.import_module("llm4free.AIbase")
    base_cls = aibase_mod.Provider

    names = list(getattr(provider_mod, "__all__", []))
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        names = [n for n in names if n in wanted]

    console.print(
        f"[bold]Webscout provider test[/bold] — {len(names)} providers, "
        f"timeout={args.timeout}s, prompt={args.prompt!r}"
    )

    results: List[ProviderResult] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    )

    with progress:
        task = progress.add_task("testing", total=len(names))
        for name in names:
            cls = getattr(provider_mod, name, None)
            if cls is None:
                results.append(ProviderResult(
                    name=name, status=INIT_FAILED, auth_required=False,
                    error_type="MissingExport",
                    error="name listed in __all__ but not present in module",
                ))
                progress.update(task, advance=1, description=f"✗ {name}")
                continue
            if not inspect.isclass(cls) or not issubclass(cls, base_cls):
                # Not a provider subclass (e.g. a utility export) — record and skip.
                results.append(ProviderResult(
                    name=name, status=INIT_FAILED, auth_required=False,
                    error_type="NotAProvider",
                    error="export is not a subclass of AIbase.Provider",
                ))
                progress.update(task, advance=1, description=f"– {name}")
                continue

            auth = bool(getattr(cls, "required_auth", False))
            if auth and not args.include_auth and not (api_keys.get(name) or default_key):
                results.append(ProviderResult(
                    name=name, status=SKIPPED_AUTH, auth_required=True,
                    error_type="AuthRequired",
                    error="use --include-auth + --api-key to test",
                ))
                progress.update(task, advance=1, description=f"… {name}")
                continue

            key = api_keys.get(name) or default_key
            progress.update(task, description=f"→ {name}")
            result = test_one_provider(name, cls, key, args.prompt, args.timeout)
            results.append(result)
            mark = {"WORKING": "✓", "EMPTY_RESPONSE": "·",
                    "INIT_FAILED": "!", "RUNTIME_ERROR": "✗",
                    "TIMEOUT": "⏱", "SKIPPED_AUTH": "…"}.get(result.status, "?")
            progress.update(task, advance=1, description=f"{mark} {name} [{result.status}]")

    console.print()
    console.print(render_summary(results))
    render_groups(results)

    # Persist
    args.out.write_text(
        json.dumps(
            {
                "prompt": args.prompt,
                "timeout_s": args.timeout,
                "results": [r.to_dict() for r in results],
                "summary": {
                    "total": len(results),
                    "working": sum(1 for r in results if r.status == WORKING),
                    "empty": sum(1 for r in results if r.status == EMPTY),
                    "init_failed": sum(1 for r in results if r.status == INIT_FAILED),
                    "runtime_error": sum(1 for r in results if r.status == RUNTIME_ERROR),
                    "timeout": sum(1 for r in results if r.status == TIMEOUT),
                    "skipped_auth": sum(1 for r in results if r.status == SKIPPED_AUTH),
                },
            },
            indent=2,
        )
    )
    console.print(f"\n[dim]Wrote {args.out}[/dim]")

    # Exit code: 0 if at least one working, 2 if nothing worked.
    s = {r.status for r in results}
    if WORKING in s:
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
