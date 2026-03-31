# Webscout Python Client
> Last updated: 2026-03-31

`webscout.client.Client` is the Python entry point for Webscout providers. It exposes a small OpenAI-style surface for chat, images, and audio speech generation while handling provider discovery, model selection, and fallback.

## Highlights

- Chat completions through `client.chat.completions.create(...)`
- Image generation through `client.images.generate(...)`
- Audio speech generation through `client.audio.speech.create(...)`
- Dynamic discovery of OpenAI-compatible, TTI, and TTS providers
- Automatic failover across matching providers
- Per-process provider instance caching

## Quick start

```python
from webscout.client import Client

client = Client(print_provider_info=True)

chat = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Summarize Webscout in one sentence."}],
)
print(chat.choices[0].message.content)

image = client.images.generate(
    prompt="A neon owl in a futuristic city",
    model="auto",
)
print(image.data[0].url)

audio_path = client.audio.speech.create(
    input_text="Hello from Webscout.",
    model="auto",
    voice="coral",
)
print(audio_path)
```

## Client options

```python
Client(
    provider=None,
    image_provider=None,
    api_key=None,
    proxies=None,
    exclude=None,
    exclude_images=None,
    exclude_tts=None,
    print_provider_info=False,
    **kwargs,
)
```

- `exclude`, `exclude_images`, and `exclude_tts` are case-insensitive provider blocklists.
- `api_key` unlocks providers that require authentication.
- `print_provider_info=True` prints the resolved provider/model pair as requests succeed.

## Provider resolution

- `model="auto"` picks a random available provider/model pair.
- `Provider/model` forces an exact provider match.
- Plain model names are matched exactly first, then fuzzily.
- If the selected provider fails, the client retries with other compatible providers.

## Audio speech generation

`client.audio.speech.create(...)` uses the TTS provider registry under `webscout/Provider/TTS/`.

- `input_text` is required.
- `model`, `voice`, `response_format`, and `instructions` are passed through to the provider.
- `stream=True` returns an iterator of audio bytes from the generated file.
- `client.audio.speech.last_provider` reports which provider last succeeded.

## Provider helpers

```python
Client.get_chat_providers()
Client.get_free_chat_providers()
Client.get_image_providers()
Client.get_free_image_providers()
Client.get_tts_providers()
Client.get_free_tts_providers()
Client.get_audio_providers()       # alias for get_tts_providers()
Client.get_free_audio_providers()  # alias for get_free_tts_providers()
```

## Debug tips

- Use `print_provider_info=True` to see resolution and failover in real time.
- Check `client.chat.completions.last_provider`, `client.images.last_provider`, and `client.audio.speech.last_provider` after a call.
- Exclude unstable providers with the relevant `exclude*` option to force fallback.

## Related docs

- [docs/models.md](models.md)
- [docs/openai-api-server.md](openai-api-server.md)
- [docs/providers/](providers/)
