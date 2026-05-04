# 🖼️ Webscout Text-to-Image (TTI) Providers

Webscout includes a collection of Text-to-Image providers that follow a common interface inspired by the OpenAI Python client. Each provider exposes an `images.create()` method which returns an `ImageResponse` object containing either image URLs or base64 data.

These providers allow you to easily generate AI‑created art from text prompts while handling image conversion and temporary hosting automatically.

## ✨ Features

- **Unified API** – Consistent `images.create()` method for all providers
- **Multiple Providers** – Generate images using different third‑party services
- **URL or Base64 Output** – Receive image URLs (uploaded to catbox.moe/0x0.st/anonfiles.com/transfer.sh) or base64 encoded bytes
- **PNG/JPEG Conversion** – Images are converted in memory to your chosen format
- **Model Listing** – Query available models with `provider.models.list()`
- **Fallback Hosting** – Automatic fallback chain for image uploads

## 📦 Supported Providers

| Provider          | Available Models (examples)               | Status    |
| ---------------- | ----------------------------------------- | --------- |
| `BingImageAI`    | `dalle3`, `mai-image-1`, `gpt4o`            | Working*  |
| `MagicHourAI`     | `general`, `photorealistic`, `anime`           | Working   |
| `PollinationsAI`  | `flux`, `flux-pro`, `turbo`, `gptimage`   | Working   |
| `MagicStudioAI`   | `magicstudio`                             | Working   |
| `TogetherImage`   | `flux.1-schnell`, `flux.1-pro`            | Working*  |

\* Requires authentication (Bing cookies or API keys).

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

### BingImageAI
- Uses Microsoft/Bing Image Creator API
- Requires Bing cookies (export from browser DevTools)
- Models:
  - `dalle3` - Good for quick, stylized art
  - `mai-image-1` - Great lighting, textures, detail
  - `gpt4o` - Consistent characters & styling
- Rate limit: ~15 images/day (free Microsoft Rewards)

```python
from webscout.Provider.TTI import BingImageAI

# Requires cookies.json file with Bing session cookies
client = BingImageAI(cookies_file="cookies.json")
response = client.images.create(
    model="dalle3",
    prompt="A cute red cat",
    n=1,
)
print(response.data[0].url)
```

### MagicHourAI (Free)
- Uses MagicHour AI free API (no API key required)
- Rate limited to ~10 requests per IP
- 16 styles available

```python
from webscout.Provider.TTI import MagicHourAI

# No API key needed!
client = MagicHourAI()
response = client.images.create(
    model="general",  # or "photorealistic", "anime", "cinematic", etc.
    prompt="A cool cyberpunk city at night",
    n=1,
    aspect_ratio="16:9",
)
print(response.data[0].url)
```

### PollinationsAI
- Allows setting a custom seed for reproducible results.

### MagicStudioAI
- Generates images through MagicStudio's public endpoint.

### TogetherImage
- High-quality image generation via Together.xyz API (Requires API Key).

### VisualGPT
- Requires cookies.json file for authentication.

## 🖥️ Image Hosting

The `image_hosting` module provides a centralized fallback chain for uploading generated images:

| Priority | Service | Max Size | Notes |
|----------|---------|----------|-------|
| 1️⃣ Primary | catbox.moe | Unlimited | Reliable, JSON API |
| 2️⃣ Secondary | 0x0.st | Unlimited | Simple, plain text response |
| 3️⃣ Tertiary | anonfiles.com | 20GB | JSON API, 14-day expiry |
| 4️⃣ Final | transfer.sh | 10GB | PUT-based, 14-day expiry |

All services require no authentication, making them ideal for TTI providers.

## 🤝 Contributing

Contributions and additional providers are welcome! Feel free to submit a pull request.