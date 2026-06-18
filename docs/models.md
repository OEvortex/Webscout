# Model Registry (`llm4free/models.py`)
> Last updated: 2025-12-20  
> Maintained by: LLM4Free Core Team

`llm4free/models.py` exposes a lightweight discovery layer so you can inspect the Large Language Model (LLM), Text-to-Speech (TTS), and Text-to-Image (TTI) offerings that ship with LLM4Free. The registry powers documentation examples (README, docs/search.md, etc.) and is useful when building UI selectors or performing health checks across providers.

## 📦 Public API

```python
from llm4free import model

model.llm.list()       # Dict[str, List[str]] mapping provider -> models
model.llm.get("Groq")  # List[str] of Groq models
model.llm.summary()    # Counts per provider

model.tts.list()       # Dict[str, voices]
model.tts.get("ElevenlabsTTS")
model.tts.summary()

model.tti.list()       # Dict[str, List[str]] for image providers
model.tti.providers()  # Detailed metadata per TTI provider
```

The object exported from `llm4free/__init__.py` is a singleton that contains `llm`, `tts`, and `tti` namespaces.

## 🧠 How It Works

- Uses `pkgutil.iter_modules` to walk through `llm4free/Provider` (for LLMs), `llm4free/Provider/TTS`, and `llm4free/Provider/TTI`.
- Detects classes derived from the relevant base class (`Provider`, `TTSProvider`, `BaseImages`).
- Prefers provider-defined metadata (e.g., `AVAILABLE_MODELS`, `get_models()`, `all_voices`). Sets are converted to lists for JSON friendliness.
- Collects additional metadata such as docstrings, supported parameters, and module names.

## 🧾 Example Usage

```python
from llm4free import model
from rich import print

summary = model.llm.summary()
print(f"Providers: {summary['providers']}, models: {summary['models']}")
print("Per-provider counts:")
for provider, count in summary['provider_model_counts'].items():
    print(f"  {provider}: {count}")

# Enumerate voices
voices = model.tts.list()
print(f"TTS providers: {len(voices)}")
print(f"Elevenlabs voices (first 5): {list(voices['ElevenLabsTTS'].items())[:5]}")

# Discover TTI metadata
print(f"TTI providers: {list(model.tti.list().keys())}")
```

## 📊 Returned Structures

### `llm.list()`
```python
{
  "Groq": ["gpt-4o-mini", "mixtral-8x7b"],
  "Meta": ["llama-3-8b", ...],
  ...
}
```

### `llm.summary()`
```python
{
  "providers": 35,
  "models": 250,
  "provider_model_counts": {
    "Groq": 6,
    "Meta": 4,
    ...
  }
}
```

### `tts.list()`
- Some providers return lists, others return `dict[str, str]` where the value is a voice ID.

### `tti.providers()`
```python
{
  "PollinationsAI": {
      "name": "PollinationsAI",
      "class": "PollinationsAI",
      "module": "pollinations",
      "models": ["flux", "flux-pro", ...],
      "parameters": ["prompt", "model", ...],
      "model_count": 5,
      "metadata": {"description": "Pollinations text-to-image provider"}
  },
  ...
}
```

## 🧩 Extending the Registry

1. **New provider class** – ensure it inherits from the correct base class (`Provider`, `TTSProvider`, or `BaseImages`).
2. **Expose models/voices** – implement `get_models()` or set `AVAILABLE_MODELS` / `all_voices`.
3. **Docstrings** – the first line becomes `metadata['description']`, so keep it meaningful.
4. **Verify** – call `model.llm.list()` (or `tts.list()`, `tti.list()`) after adding a provider to confirm it appears.

## 🔗 Related Docs

- [docs/client.md](client.md) – the unified client uses `_get_models_safely()` to enhance model resolution.
- [Provider.md](../Provider.md) – cross-reference provider locations and normal vs OpenAI-compatible implementations.
- [docs/architecture.md](architecture.md) – where the registry fits within the overall system.
