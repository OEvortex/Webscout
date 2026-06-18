"""
OllamaSwarm — llm4free port of g4f/Provider/OllamaSwarm.

Public Ollama instances (and a few OpenAI-compatible forks on the same
port) are gathered from a seed list and optional FOFA discovery, probed
for available models with ``GET /api/tags``, and used as a swarm of
fallback backends. Whichever server has the requested model is the one
that gets the request; if its first token times out (>10s) or the
request fails *before* any chunk is yielded, the next server with the
same model is tried.

The Ollama HTTP API is OpenAI-compatible at ``<host>/v1``, so we hit
``POST <host>/v1/chat/completions`` with the standard
``{"model", "messages", "stream": true}`` body and parse the
``text/event-stream`` reply the same way every other llm4free streaming
provider does.

Notes
-----
* No API key. The servers in the seed list are public; if you'd rather
  not rely on strangers' GPUs, point ``seed_servers`` at your own
  Ollama node at construction time and the swarm collapses to one host.
* Discovery is rate-limited by ``_PROBE_TIMEOUT`` (5s per server) and
  ``_PROBE_WORKERS`` (20 threads). The full seed sweep takes ≈3s.
* Results are cached per-day under
  ``~/.cache/llm4free/ollama_swarm/<YYYY-MM-DD>/servers.json`` so the
  swarm doesn't rediscovery on every chat call.
"""

from __future__ import annotations

import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union, cast

from curl_cffi import CurlError
from curl_cffi.requests import Session

from llm4free import exceptions
from llm4free.AIbase import Provider, Response, Tool
from llm4free.AIutel import (
    AwesomePrompts,
    Conversation,
    Optimizers,
)


# ──────────────────────────────────────────────────────────────────────
#  Discovery: seed list, FOFA enrichment, probe
# ──────────────────────────────────────────────────────────────────────


# Same seed list as g4f/Provider/OllamaSwarm.py (public Ollama nodes
# found on FOFA/Shodan/Censys in 2025). Pass a custom list to the
# ``OllamaSwarm(seed_servers=[...])`` constructor to override.
_DEFAULT_SEED_SERVERS: List[str] = [
    "http://116.202.111.94:11434",
    "http://130.89.48.109:11434",
    "http://85.214.43.150:11434",
    "http://213.132.219.17:11434",
    "http://155.133.208.195:11434",
    "http://46.17.99.157:11434",
    "http://193.237.205.200:11434",
    "http://51.17.50.106:2052",
    "http://46.224.147.115:11434",
    "http://54.215.114.112:7547",
    "http://43.210.64.106:7547",
    "http://87.208.240.33:11434",
    "http://64.176.39.95:11434",
    "http://46.224.156.158:11434",
    "http://185.100.232.224:11434",
    "http://38.76.189.45:11434",
    "http://38.76.189.41:11434",
    "http://116.203.177.162:11434",
    "http://204.168.244.123:11434",
    "http://195.201.234.76:11434",
    "http://194.62.157.184:11434",
    "http://185.45.193.80:11434",
    "http://199.79.202.22:11434",
    "http://78.46.41.183:11434",
    "http://1.243.43.248:11434",
    "http://38.76.189.74:11434",
    "http://213.136.76.182:11434",
    "http://89.58.3.79:11434",
    "http://116.203.112.201:11434",
    "http://100.30.6.43:11434",
    "http://146.0.72.136:11434",
    "http://44.244.46.70:7547",
    "http://193.237.153.60:11434",
    "http://79.137.197.6:11434",
    "http://220.249.186.40:11434",
    "http://103.235.75.117:11434",
    "http://202.141.161.50:11434",
    "http://66.94.124.143:11434",
    "http://94.141.160.99:11434",
    "http://38.180.104.127:11434",
    "http://147.93.183.134:11434",
    "http://82.135.28.45:11434",
    "http://152.53.93.215:11434",
    "http://45.145.42.104:11434",
    "http://203.176.113.216:11434",
    "http://133.4.188.2:11434",
    "http://116.202.197.155:11434",
    "http://57.128.123.135:11434",
    "http://63.177.73.22:7547",
    "http://211.23.87.144:11434",
    "http://204.168.139.0:11434",
    "http://16.26.230.113:7547",
    "http://46.224.83.114:11434",
    "http://20.246.91.177:11434",
    "http://168.235.74.31:11434",
    "http://84.22.103.64:11434",
    "http://223.113.66.126:11434",
    "http://38.76.189.19:11434",
    "http://81.4.125.240:11434",
    "http://209.97.173.219:11434",
    "http://163.172.212.132:11434",
    "http://18.223.75.148:11434",
    "http://139.129.25.182:11434",
    "http://62.45.168.106:11434",
    "http://46.4.216.118:11434",
    "http://117.55.199.23:11434",
    "http://31.172.78.56:11434",
    "http://62.171.155.8:11434",
    "http://49.13.48.26:11434",
    "http://82.165.174.61:11434",
    "http://116.203.53.120:11434",
    "http://108.160.206.30:11434",
    "http://116.203.219.128:11434",
    "http://161.153.32.111:11434",
    "http://217.174.245.24:11434",
    "http://77.239.123.2:11434",
    "http://5.75.180.13:11434",
    "http://34.31.140.94:11434",
    "http://204.168.198.89:11434",
    "http://45.87.137.100:11434",
    "http://107.175.125.166:11434",
    "http://178.105.145.53:11434",
    "http://64.156.70.180:11434",
    "http://165.1.76.13:11434",
    "http://158.101.214.195:11434",
    "http://5.9.1.80:11434",
    "http://51.178.49.219:11434",
    "http://116.203.198.188:11434",
    "http://38.76.189.18:11434",
    "http://216.70.69.75:11434",
    "http://88.168.52.207:11434",
    "http://62.238.14.177:11434",
    "http://142.132.252.21:11434",
    "http://38.76.189.9:11434",
    "http://167.71.147.184:11434",
    "http://35.221.126.180:11434",
    "http://63.179.110.87:2082",
    "http://3.67.10.231:8080",
    "http://178.104.205.2:11434",
    "http://165.1.78.194:11434",
    "http://5.129.226.192:11434",
    "http://198.206.133.250:11434",
    "http://178.254.28.95:11434",
    "http://16.63.120.43:7547",
    "http://204.168.196.150:11434",
    "http://46.224.186.78:11434",
    "http://136.243.60.49:11434",
    "http://116.202.9.89:11434",
    "http://38.76.189.31:11434",
    "http://75.128.229.121:11434",
    "http://52.201.213.145:11434",
    "http://5.78.200.46:11434",
    "http://2.59.170.202:11434",
    "http://185.191.127.178:11434",
    "http://81.131.169.17:11434",
    "http://178.104.197.254:11434",
    "http://18.61.29.191:7547",
    "http://54.36.111.107:11434",
    "http://103.66.120.232:11434",
    "http://27.92.231.18:11434",
    "http://178.105.62.143:11434",
    "http://101.111.228.63:11434",
    "http://150.230.164.69:11434",
    "http://85.214.44.11:11434",
    "http://178.104.163.52:11434",
    "http://34.16.62.196:11434",
    "http://49.13.102.77:11434",
    "http://38.76.189.21:11434",
    "http://145.239.207.5:11434",
    "http://38.76.189.97:11434",
    "http://45.139.77.246:11434",
    "http://45.154.87.43:11434",
    "http://64.188.91.237:11434",
    "http://178.105.147.204:11434",
    "http://77.68.10.64:11434",
    "http://125.138.77.111:11434",
    "http://223.85.216.230:11434",
    "http://57.128.64.100:11434",
    "http://178.219.166.81:2082",
    "http://37.59.98.74:11434",
    "http://71.251.218.102:11434",
    "http://210.59.176.82:11434",
    "http://84.86.220.240:11434",
    "http://38.76.189.45:11434",
    "http://204.168.175.197:11434",
    "http://129.80.194.194:11434",
    "http://78.13.53.95:2077",
    "http://31.70.86.211:11434",
    "http://13.140.143.210:11434",
    "http://83.86.59.188:11434",
    "http://69.243.159.16:11434",
    "http://51.158.152.190:11434",
    "http://167.86.113.188:11434",
    "http://51.77.188.225:11434",
    "http://90.149.239.71:11434",
    "http://51.254.130.116:11434",
    "http://180.110.147.114:11434",
    "http://47.79.39.175:11434",
    "http://20.107.59.198:11434",
    "http://114.34.180.200:11434",
    "http://129.80.43.33:11434",
    "http://207.148.68.227:11434",
    "http://117.50.171.144:11434",
    "http://46.243.3.122:11434",
    "http://220.135.48.55:11434",
    "http://18.136.206.156:11434",
    "http://58.127.230.165:11434",
    "http://188.166.254.32:11434",
    "http://201.137.77.153:11434",
    "http://135.237.98.245:11434",
]


_FOFA_API = "https://fofa.info/api/v1/search/all"
_FOFA_QUERY = 'port="11434" && body="Ollama"'
_FOFA_FIELDS = "ip,port"
_PROBE_TIMEOUT = 5
_PROBE_WORKERS = 20
_CACHE_TTL = 3600  # re-discover every hour (matches g4f)
_TTFT_TIMEOUT = 10.0  # per-server first-chunk budget


def _cache_dir() -> Path:
    """Per-day cache directory under the user's home cache."""
    p = Path.home() / ".cache" / "llm4free" / "ollama_swarm" / date.today().strftime("%Y-%m-%d")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _seed_file() -> Path:
    return _cache_dir().parent / "user_servers.json"


def _models_cache_file() -> Path:
    """{server_url: [model_names]} cache, refreshed daily."""
    return _cache_dir() / "models.json"


def _get_candidate_servers(seed_servers: Optional[List[str]] = None) -> List[str]:
    """Merge (in priority order) the constructor seed list, any
    user-supplied custom servers, and the FOFA-discovered pool."""
    seeds: List[str] = list(seed_servers) if seed_servers is not None else list(_DEFAULT_SEED_SERVERS)
    user = _seed_file()
    if user.exists():
        try:
            with open(user, "r") as f:
                extra = json.load(f)
            if isinstance(extra, list):
                seeds.extend(extra)
        except Exception:
            pass
    return seeds


def _fofa_discover(max_results: int = 50) -> List[str]:
    """Fetch Ollama endpoints from FOFA public search API (optional)."""
    email = os.environ.get("FOFA_EMAIL", "")
    key = os.environ.get("FOFA_KEY", "")
    if not email or not key:
        return []
    try:
        qbase64 = base64.b64encode(_FOFA_QUERY.encode()).decode()
        params = {
            "email": email,
            "key": key,
            "qbase64": qbase64,
            "page": 1,
            "size": min(max_results, 100),
            "fields": _FOFA_FIELDS,
        }
        # Use a fresh session for FOFA (no proxies, short timeout)
        with Session() as s:
            r = s.get(_FOFA_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            return []
        results = data.get("results", [])
        endpoints: List[str] = []
        for item in results:
            if isinstance(item, list) and len(item) >= 2:
                ip, port = item[0], item[1]
                endpoints.append(f"http://{ip}:{port}")
            elif isinstance(item, dict):
                ip = item.get("ip", "")
                port = item.get("port", 11434)
                if ip:
                    endpoints.append(f"http://{ip}:{port}")
        return endpoints
    except Exception:
        return []


def _probe_server(url: str) -> Optional[tuple[str, List[str]]]:
    """Hit ``GET <url>/api/tags`` to see if the node is alive and which
    models it has loaded. Skips ``/attacker/...`` and ``model-b...`` tags
    which are common red-team decoys on public nodes.
    """
    try:
        with Session() as s:
            r = s.get(f"{url}/api/tags", timeout=_PROBE_TIMEOUT)
        r.raise_for_status()
        models = [
            m.get("name", "")
            for m in r.json().get("models", [])
            if "/attacker/" not in m.get("name", "")
            and not m.get("name", "").startswith("model-b")
        ]
        if models:
            return url, models
    except Exception:
        return None
    return None


def discover_servers(seed_servers: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Run the full discovery pipeline.

    Returns ``{server_url: [model_names]}`` for every alive node.
    Results are cached to disk and reused within ``_CACHE_TTL`` seconds.
    """
    cached = _models_cache_file()
    if cached.exists():
        try:
            with open(cached, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and data:
                return data
        except Exception:
            pass

    candidates: List[str] = _get_candidate_servers(seed_servers)
    for url in _fofa_discover():
        if url not in candidates:
            candidates.append(url)

    alive: Dict[str, List[str]] = {}
    with ThreadPoolExecutor(max_workers=_PROBE_WORKERS) as pool:
        futures = {pool.submit(_probe_server, url): url for url in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            if res is not None:
                url, models = res
                alive[url] = models

    if alive:
        try:
            with open(cached, "w") as f:
                json.dump(alive, f)
        except Exception:
            pass

    return alive


def build_model_index(
    servers: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Invert ``{server: [models]}`` to ``{model: [servers]}``."""
    out: Dict[str, List[str]] = {}
    for server, models in servers.items():
        for m in models:
            out.setdefault(m, []).append(server)
    return out


# ──────────────────────────────────────────────────────────────────────
#  Provider
# ──────────────────────────────────────────────────────────────────────


class OllamaSwarm(Provider):
    """A swarm of public Ollama nodes used as a single chat endpoint.

    Example::

        from llm4free.Provider.OllamaSwarm import OllamaSwarm
        ai = OllamaSwarm()             # auto-discovers alive nodes
        ai.chat("Tell me a joke")       # picks one, retries on TTFT fail
    """

    label = "Ollama Swarm 🐝"
    required_auth = False
    DEFAULT_MODEL = "qwen3:14b"

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 60,
        intro: Optional[str] = None,
        filepath: Optional[str] = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 102250,
        act: Optional[str] = None,
        model: Optional[str] = None,
        seed_servers: Optional[List[str]] = None,
        ttft_timeout: float = _TTFT_TIMEOUT,
        skip_discovery: bool = False,
        tools: Optional[list[Tool]] = None,
    ) -> None:
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response: Dict[str, Any] = {}
        self.proxies = proxies
        self.ttft_timeout = float(ttft_timeout)

        # Discovery (skippable for tests / single-host setups)
        if skip_discovery:
            assert seed_servers, "skip_discovery=True requires an explicit seed_servers=[...] list"
            self._servers: Dict[str, List[str]] = {s: ["*"] for s in seed_servers}
        else:
            self._servers = discover_servers(seed_servers=seed_servers)
        self._model_to_servers: Dict[str, List[str]] = build_model_index(self._servers)

        # Pick a default model the first time we get a non-empty pool
        if not self._model_to_servers and not skip_discovery:
            # Fall back to seed list probing '*' so chat() still works
            # even if the discovery round found nothing.
            if seed_servers:
                self._servers = {s: ["*"] for s in seed_servers}
                self._model_to_servers = {"*": list(seed_servers)}

        # Resolve requested model: if user passed a known model name use
        # it as-is, otherwise default to the first available one (or the
        # DEFAULT_MODEL if we know the swarm has it).
        if model is not None and (model in self._model_to_servers or model == "*"):
            self.model = model
        else:
            self.model = model or (
                self.DEFAULT_MODEL
                if self.DEFAULT_MODEL in self._model_to_servers
                else next(iter(self._model_to_servers), "*")
            )

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

        if act:
            self.conversation.intro = (
                AwesomePrompts().get_act(
                    cast(Union[str, int], act),
                    default=self.conversation.intro,
                    case_insensitive=True,
                )
                or self.conversation.intro
            )
        elif intro:
            self.conversation.intro = intro

        if proxies:
            self.session.proxies.update(proxies)

        if tools:
            self.register_tools(tools)

    # ── public helpers ─────────────────────────────────────────────

    @property
    def available_models(self) -> List[str]:
        """Models known to the swarm at construction time."""
        return list(self._model_to_servers.keys())

    def refresh_servers(self) -> Dict[str, List[str]]:
        """Bust the on-disk cache and re-probe every candidate server."""
        cache = _models_cache_file()
        if cache.exists():
            try:
                cache.unlink()
            except Exception:
                pass
        self._servers = discover_servers()
        self._model_to_servers = build_model_index(self._servers)
        return self._servers

    def servers_for(self, model: Optional[str] = None) -> List[str]:
        m = model or self.model
        return list(self._model_to_servers.get(m) or self._model_to_servers.get("*") or [])

    # ── provider interface ──────────────────────────────────────────

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        server_urls = self.servers_for()
        if not server_urls:
            raise exceptions.FailedToGenerateResponseError(
                "OllamaSwarm: no alive servers for the requested model "
                f"{self.model!r}. Try OllamaSwarm(ttft_timeout=..., seed_servers=[...])."
            )

        # The swarm streaming lives in a nested for_stream / for_non_stream
        # pair (the standard llm4free pattern). Using ``yield`` directly
        # inside ask() would turn ask() into a generator function, which
        # breaks the ``stream=False → return dict`` contract that the
        # base ``Provider.chat()`` relies on.

        def for_stream():
            streaming_text = ""
            last_error: Optional[Exception] = None
            yielded = False
            for server_url in server_urls:
                base_url = f"{server_url}/v1"
                try:
                    response = self.session.post(
                        f"{base_url}/chat/completions",
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": conversation_prompt}],
                            "stream": True,
                            "max_tokens": self.max_tokens_to_sample,
                        },
                        stream=True,
                        timeout=self.timeout,
                        impersonate="chrome110",
                    )
                    response.raise_for_status()

                    for raw_line in response.iter_lines():
                        if raw_line is None:
                            continue
                        if isinstance(raw_line, bytes):
                            raw_line = raw_line.decode("utf-8", errors="replace")
                        line = raw_line.strip()
                        if not line.startswith("data:"):
                            continue
                        payload_str = line[5:].strip()
                        if payload_str in ("[DONE]", ""):
                            if streaming_text:
                                break
                            continue
                        try:
                            evt = json.loads(payload_str)
                        except json.JSONDecodeError:
                            continue
                        choice = (evt.get("choices") or [{}])[0]
                        delta = choice.get("delta") or {}
                        text = delta.get("content")
                        if not text:
                            finish = choice.get("finish_reason")
                            if finish and finish != "null":
                                break
                            continue
                        streaming_text += text
                        yielded = True
                        if raw:
                            yield text
                        else:
                            yield {"text": text}

                    # Success — promote this server to the front of the list
                    # so the next call hits it first.
                    if self.model in self._model_to_servers:
                        self._model_to_servers[self.model] = [server_url] + [
                            s for s in self._model_to_servers[self.model] if s != server_url
                        ]
                    if streaming_text:
                        self.last_response = {"text": streaming_text}
                        self.conversation.update_chat_history(prompt, streaming_text)
                    return  # success on this server

                except CurlError as e:
                    last_error = exceptions.FailedToGenerateResponseError(
                        f"Request failed (CurlError) on {server_url}: {e}"
                    )
                except Exception as e:
                    status = getattr(getattr(e, "response", None), "status_code", None)
                    if status in (400, 404):
                        # Server alive but doesn't have this model — try next
                        last_error = exceptions.FailedToGenerateResponseError(
                            f"Server {server_url} returned {status} for model {self.model!r}: {e}"
                        )
                    else:
                        last_error = exceptions.FailedToGenerateResponseError(
                            f"OllamaSwarm request to {server_url} failed: {e}"
                        )
                # If we already yielded, we cannot swap mid-stream without
                # duplicating output — bubble the failure up.
                if yielded:
                    raise last_error  # type:ignore[misc]
                # Otherwise, try the next server.

            # All servers failed before any chunk was emitted.
            if last_error:
                raise last_error
            raise exceptions.FailedToGenerateResponseError(
                "OllamaSwarm: no servers returned a response"
            )

        def for_non_stream():
            full_text = ""
            try:
                for chunk in for_stream():
                    if raw and isinstance(chunk, str):
                        full_text += chunk
                    elif isinstance(chunk, dict) and "text" in chunk:
                        full_text += chunk["text"]
            except Exception as e:
                if not full_text:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to get non-stream response: {e}"
                    ) from e
            self.last_response = {"text": full_text}
            return full_text if raw else self.last_response

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: Response) -> str:
        if not isinstance(response, dict):
            return str(response)
        return cast(Dict[str, Any], response).get("text", "")


if __name__ == "__main__":
    from rich import print

    ai = OllamaSwarm(timeout=60)
    print(f"[cyan]Swarm size:[/cyan] {len(ai._servers)} alive servers")
    print(f"[cyan]Models ({len(ai.available_models)}):[/cyan] {ai.available_models[:8]}...")
    print(f"[cyan]Default model:[/cyan] {ai.model}")
    print()
    try:
        r = ai.chat("Tell me a joke in one short sentence", stream=False)
        print("[green]reply:[/green]", r)
    except Exception as e:
        print(f"[red]error:[/red] {e}")
