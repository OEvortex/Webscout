# 🖼️ Webscout Text-to-Image (TTI) Providers

Webscout includes a collection of Text-to-Image providers that follow a common interface inspired by the OpenAI Python client. Each provider exposes an `images.create()` method which returns an `ImageResponse` object containing either image URLs or base64 data.

These providers allow you to easily generate AI‑created art from text prompts while handling image conversion and temporary hosting automatically.

## ✨ Features

- **Unified API** – Consistent `images.create()` method for all providers
- **Multiple Providers** – Generate images using different third‑party services
- **URL or Base64 Output** – Receive image URLs (uploaded to catbox.moe/0x0.st) or base64 encoded bytes
- **PNG/JPEG Conversion** – Images are converted in memory to your chosen format
- **Model Listing** – Query available models with `provider.models.list()`

## 📦 Supported Providers

| Provider         | Available Models (examples)               | Status    |
| ---------------- | ----------------------------------------- | --------- |
| `PollinationsAI` | `flux`, `flux-pro`, `turbo`, `gptimage`   | Working   |
| `MagicStudioAI`  | `magicstudio`                             | Working   |
| `TogetherImage`  | `flux.1-schnell`, `flux.1-pro`            | Working*  |

\* Requires authentication (API keys).

> **Note**: Some providers require the `Pillow` package for image processing.

## 🚀 Quick Start

```python
from webscout.Provider.TTI import PollinationsAI

# Initialize the provider
client = PollinationsAI()

# Generate two images and get URLs
response = client.images.create(
    model="flux",
    prompt="A futuristic city skyline at sunset",
    n=2,
    response_format="url"
)

print(response)
```

### Base64 Output

If you prefer the raw image data:

```python
response = client.images.create(
    model="flux",
    prompt="Crystal mountain landscape",
    response_format="b64_json"
)
# `response.data` will contain base64 strings
```

## 🔧 Provider Specifics

- **PollinationsAI** – Allows setting a custom seed for reproducible results.
- **MagicStudioAI** – Generates images through MagicStudio's public endpoint.
- **TogetherImage** – High-quality image generation via Together.xyz API (Requires API Key).

## 🤝 Contributing

Contributions and additional providers are welcome! Feel free to submit a pull request.