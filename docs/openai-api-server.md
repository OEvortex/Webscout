# OpenAI-Compatible API Server (`llm4free.server`)
> Last updated: 2025-12-20
> Maintained by [LLM4Free](https://github.com/OEvortex/LLM4Free)

LLM4Free's [`llm4free.server`](../llm4free/server/__init__.py:1) module provides a comprehensive OpenAI-compatible API server that serves AI models in OpenAI-compatible API format, making it usable wherever OpenAI API is expected. This server allows you to use any supported LLM4Free provider with tools and applications designed for OpenAI's API. The server exposes the same providers available in the LLM4Free Python client (`client.py`) through HTTP endpoints, enabling integration with any OpenAI-compatible application. For client-side integrations, see [docs/client.md](client.md).

## Table of Contents

1. [Core Components](#core-components)
2. [Server Configuration](#server-configuration)
3. [Provider Management](#provider-management)
4. [API Endpoints](#api-endpoints)
5. [Starting the Server](#starting-the-server)
6. [Usage Examples](#usage-examples)
7. [Environment Variables](#environment-variables)
8. [Error Handling](#error-handling)
9. [Custom UI & Documentation](#custom-ui--documentation)
10. [Integration Guide](#integration-guide)

## Core Components

### [`server.py`](../llm4free/server/server.py:1)

The main server module that creates and configures the FastAPI application with OpenAI-compatible endpoints.

```python
from llm4free.server.server import create_app, run_api, start_server

# Create FastAPI app
app = create_app()

# Start server programmatically
start_server(port=8000, host="0.0.0.0")
```

**Key Features:**
- OpenAI-compatible API endpoints (v1/chat/completions, v1/models, etc.)
- Automatic provider discovery and registration
- Comprehensive error handling and logging
- Interactive API documentation with custom UI
- Support for streaming and non-streaming responses
- Dynamic configuration through environment variables

## Server Configuration

### [`ServerConfig`](../llm4free/server/config.py:22)

Centralized configuration management for the API server.

```python
from llm4free.server.config import ServerConfig

config = ServerConfig()
config.update(
    port=8000,
    host="0.0.0.0",
    debug=False,
    request_logging_enabled=True
)
```

**Configuration Options:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"0.0.0.0"` | Server host address |
| `port` | `int` | `8000` | Server port number |
| `debug` | `bool` | `False` | Enable debug mode |
| `cors_origins` | `List[str] | `["*"]` | CORS allowed origins |
| `max_request_size` | `int` | `10MB` | Maximum request size |
| `request_timeout` | `int` | `300` | Request timeout in seconds |
| `auth_required` | `bool` | `False` | Require authentication |
| `rate_limit_enabled` | `bool` | `False` | Enable rate limiting |
| `request_logging_enabled` | `bool` | `True` (via env) | Enable request logging |

## Provider Management

### [`providers.py`](../llm4free/server/providers.py:1)

Automatic provider discovery and management system with intelligent model resolution. The server dynamically discovers all OpenAI-compatible and TTI providers that don't require authentication.

```python
from llm4free.server.providers import (
    initialize_provider_map,
    initialize_tti_provider_map,
    resolve_provider_and_model,
    resolve_tti_provider_and_model,
    get_provider_instance,
    get_tti_provider_instance
)

# Initialize all providers at startup
initialize_provider_map()
initialize_tti_provider_map()

# Resolve provider and model at runtime
provider_class, model_name = resolve_provider_and_model("ChatGPT/gpt-4o")

# Get cached provider instance (reused across requests)
provider = get_provider_instance(provider_class)
```

**Key Features:**
- Discovers providers automatically at startup from `llm4free.Provider.OPENAI`
- Initializes only providers with `required_auth=False`
- Creates provider instance cache to avoid reinitialization overhead
- Supports both chat completion and text-to-image provider discovery
- Handles model-to-provider mapping including provider-specific model names

**Provider Features:**
- Automatic discovery of OpenAI-compatible providers
- Model validation and availability checking
- Provider instance caching for performance
- Support for both chat and image generation providers
- Fallback provider configuration

## API Endpoints

The server provides OpenAI-compatible API endpoints that mirror the OpenAI API specification, allowing drop-in replacement for applications that use OpenAI's API.

### Chat Completions

**Endpoint:** `POST /v1/chat/completions`

This endpoint supports the full OpenAI chat completions API specification, including streaming and non-streaming responses, message history, and model selection.

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Content-Type": "application/json"
    },
    json={
        "model": "ChatGPT/gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 150,
        "stream": False
    }
)
```

**Supported Parameters:**
- `model`: Provider/model format (e.g., "ChatGPT/gpt-4o", "Toolbaz/grok-4.1-fast")
- `messages`: List of message objects with role and content
- `temperature`, `top_p`, `n`, `stream`, `max_tokens`, `presence_penalty`, `frequency_penalty`, `logit_bias`, `user`, `stop`
- Multimodal content support (text and image URLs)

### Image Generation

**Endpoint:** `POST /v1/images/generations`

OpenAI-compatible image generation endpoint with support for multiple text-to-image providers.

```python
response = requests.post(
    "http://localhost:8000/v1/images/generations",
    headers={
        "Content-Type": "application/json"
    },
    json={
        "prompt": "A futuristic cityscape at sunset, digital art",
        "model": "PollinationsAI/flux",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
        "style": "default",  # Provider-specific parameter
        "seed": 12345        # Provider-specific parameter
    }
)
```

**Supported Parameters:**
- `prompt`: Text description of the desired image
- `model`: TTI provider/model format (e.g., "PollinationsAI/flux", "LeonardoAI/leonardo-ai")
- `n`: Number of images to generate (1-10)
- `size`: Image dimensions ("256x256", "512x512", "1024x1024")
- `response_format`: "url" or "b64_json"
- Additional provider-specific parameters (style, aspect_ratio, timeout, image_format, seed)

### Model Listing

**Endpoint:** `GET /v1/models`

Lists all available models from providers that are automatically discovered and registered at startup.

```python
response = requests.get(
    "http://localhost:8000/v1/models"
)

# Response includes all provider/model combinations
available_models = response.json()["data"]
for model in available_models:
    print(f"ID: {model['id']}, Owned by: {model['owned_by']}")
```

### Additional Endpoints

**Provider Information:** `GET /v1/providers`
Provides detailed information about all available providers including their supported models and parameters.

**Web Search:** `GET /search`
Unified web search endpoint supporting multiple search engines (DuckDuckGo, Google, Bing, etc.) with various search types.

**Search Provider Info:** `GET /search/provider`
Provides details about available search providers and their supported categories and parameters.

## Starting the Server

### Command Line Interface

The server provides a comprehensive CLI with environment variable support. The server can be started using the console script:

```bash
# Basic startup
llm4free-server

# Custom configuration
llm4free-server --port 8080 --host 127.0.0.1 --debug

# Production settings
llm4free-server --port 8000 --host 0.0.0.0 --workers 4 --log-level info
```

**CLI Options:**
- `--port`: Port to run the server on (default: 8000)
- `--host`: Host to bind the server to (default: 0.0.0.0)
- `--workers`: Number of worker processes (default: 1)
- `--log-level`: Log level (debug, info, warning, error, critical) (default: info)
- `--default-provider`: Default provider to use (optional)
- `--base-url`: Base URL for the API (e.g., /api/v1) (optional)
- `--debug`: Run in debug mode (optional)

### Programmatic Startup

```python
from llm4free.server import start_server, run_api

# Simple startup with defaults
start_server()

# Advanced configuration
start_server(
    port=8080,
    host="0.0.0.0",
    workers=2,
    log_level="debug",
    debug=True
)

# Full control with run_api
run_api(
    host="0.0.0.0",
    port=8000,
    workers=1,
    log_level="info",
    debug=False,
    default_provider="ChatGPT",
    base_url="/api/v1"
)
```

### Alternative Methods

```bash
# Using Python module directly
python -m llm4free.server.server

# Using Python module with arguments
python -m llm4free.server.server --port 8080 --debug

# Direct execution
python llm4free/server/server.py --host localhost --port 9000
```

### Docker Deployment

The server includes comprehensive Docker support with multiple deployment profiles:

```bash
# Basic Docker deployment
docker run -p 8000:8000 llm4free-api

# With custom configuration
docker run -p 8080:8080 -e LLM4FREE_PORT=8080 -e LLM4FREE_LOG_LEVEL=debug llm4free-api

# Using Docker Compose
docker-compose up llm4free-api

# Production deployment with Gunicorn
docker-compose --profile production up llm4free-api-production
```

For detailed Docker deployment instructions, see [DOCKER.md](../DOCKER.md).

## Usage Examples

### OpenAI Python Client

The server is fully compatible with the official OpenAI Python client, allowing for easy drop-in replacement:

```python
from openai import OpenAI

# Initialize client with server URL
client = OpenAI(
    api_key="dummy-key", # API key is not required but may be expected by the client
    base_url="http://localhost:8000/v1"
)

# Chat completion with specific provider/model
response = client.chat.completions.create(
    model="ChatGPT/gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)

# Using 'auto' selection (if provider supports it)
response = client.chat.completions.create(
    model="auto",  # Will use server's default provider
    messages=[
        {"role": "user", "content": "What is machine learning?"}
    ]
)
```

### Streaming Responses

Streaming works exactly like with the OpenAI API:

```python
# Streaming chat completion
stream = client.chat.completions.create(
    model="ChatGPT/gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a short poem"}],
    stream=True
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print()  # New line after completion
```

### Image Generation

```python
# Generate images using TTI providers
response = client.images.generate(
    model="PollinationsAI/flux",
    prompt="A majestic mountain landscape at sunrise",
    n=1,
    size="1024x1024",
    response_format="url"  # or "b64_json"
)

print(f"Generated image URL: {response.data[0].url}")
```

### cURL Examples

```bash
# Chat completion with specific provider
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ChatGPT/gpt-4o",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'

# Image generation
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cyberpunk city at night",
    "model": "PollinationsAI/flux",
    "n": 1,
    "size": "1024x1024",
    "response_format": "url"
  }'

# List available models
curl http://localhost:8000/v1/models

# Get provider information
curl http://localhost:8000/v1/providers
```

### JavaScript/Node.js Client

```javascript
// Using fetch API or any HTTP client
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'ChatGPT/gpt-4o',
    messages: [
      { role: 'user', content: 'Hello, world!' }
    ],
    temperature: 0.7
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

## Environment Variables

The server supports comprehensive environment variable configuration through both direct environment variables and Docker. All environment variables are read at startup and used to configure the ServerConfig.

### Server Configuration

```bash
# Server settings
export LLM4FREE_HOST="0.0.0.0"          # Server host address (default: 0.0.0.0)
export LLM4FREE_PORT="8000"             # Server port (default: 8000)
export LLM4FREE_WORKERS="1"             # Number of worker processes (default: 1)
export LLM4FREE_LOG_LEVEL="info"        # Log level: debug, info, warning, error (default: info)
export LLM4FREE_DEBUG="false"           # Enable debug mode (default: false)

# Optional API configuration
export LLM4FREE_DEFAULT_PROVIDER="ChatGPT"  # Default provider (default: ChatGPT)
export LLM4FREE_BASE_URL="/api/v1"          # Base URL for API (optional)
export LLM4FREE_DATA_DIR="/app/data"        # Data directory (default: /app/data)

# API Metadata (for documentation)
export LLM4FREE_API_TITLE="LLM4Free OpenAI API"                    # API title
export LLM4FREE_API_DESCRIPTION="OpenAI API compatible interface for various LLM providers"  # API description
export LLM4FREE_API_VERSION="0.2.0"           # API version
export LLM4FREE_API_DOCS_URL="/docs"          # Documentation URL (default: /docs)
export LLM4FREE_API_REDOC_URL="/redoc"        # ReDoc URL (default: /redoc)
export LLM4FREE_API_OPENAPI_URL="/openapi.json"  # OpenAPI spec URL (default: /openapi.json)

# Advanced configuration
export LLM4FREE_REQUEST_LOGGING="true"        # Enable request logging (default: true)
export LLM4FREE_CORS_ORIGINS="*"              # CORS allowed origins (default: "*")
```

### Configuration Priority

The server follows this configuration priority:
1. Command-line arguments (highest priority)
2. Environment variables
3. Code defaults (lowest priority)

For a complete list of supported environment variables and Docker deployment options, see [DOCKER.md](../DOCKER.md).

## Error Handling

### [`APIError`](../llm4free/server/exceptions.py:26)

Comprehensive error handling with OpenAI-compatible error responses.

```python
from llm4free.server.exceptions import APIError
from starlette.status import HTTP_400_BAD_REQUEST

# Raise API error
raise APIError(
    message="Invalid model specified",
    status_code=HTTP_400_BAD_REQUEST,
    error_type="invalid_request_error",
    param="model",
    code="model_not_found"
)
```

**Error Response Format:**
```json
{
  "error": {
    "message": "Invalid model specified",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found",
    "footer": "If you believe this is a bug, please file an issue at https://github.com/OEvortex/LLM4Free."
  }
}
```

### Exception Handling

The server provides comprehensive exception handling with detailed error responses for different error types:

```python
# Validation errors
{
  "error": {
    "message": "Request validation error.",
    "details": [
      {
        "loc": ["body", "messages"],
        "message": "field required at body -> messages",
        "type": "value_error.missing"
      }
    ],
    "type": "validation_error",
    "footer": "If you believe this is a bug, please file an issue at https://github.com/OEvortex/LLM4Free."
  }
}

# HTTP errors
{
  "error": {
    "message": "Something went wrong.",
    "type": "http_error",
    "footer": "If you believe this is a bug, please file an issue at https://github.com/OEvortex/LLM4Free."
  }
}

# General server errors
{
  "error": {
    "message": "Internal server error: Details about the error",
    "type": "server_error",
    "footer": "If you believe this is a bug, please file an issue at https://github.com/OEvortex/LLM4Free."
  }
}

## Custom UI & Documentation

The server includes custom UI elements and documentation features:

### Landing Page
The root endpoint (`/`) serves a custom landing page with information about the LLM4Free API server and available features.

### API Documentation
- `/docs`: Custom Swagger UI with LLM4Free branding and GitHub footer
- `/redoc`: ReDoc documentation interface
- `/openapi.json`: OpenAPI specification

The documentation includes a custom CSS theme and a footer linking to the GitHub repository.

## Integration Guide

### Using with Existing OpenAI Applications

Since the server provides fully OpenAI-compatible APIs, you can replace OpenAI API URLs in existing applications:

1. **Update base URL**: Change from `https://api.openai.com/v1` to `http://your-server:8000/v1`
2. **Model names**: Use LLM4Free provider/model format (e.g., "ChatGPT/gpt-4o", "Toolbaz/grok-4.1-fast")
3. **API key**: API key is not required but may be expected by some clients

### Client Compatibility

The server is compatible with:
- Official OpenAI Python client
- OpenAI JavaScript/TypeScript client
- Any HTTP client that supports OpenAI API format
- Third-party tools and applications that work with OpenAI API

### Provider Selection Strategy

When using provider/model pairs:
- Format: `ProviderName/model_name` (e.g., "ChatGPT/gpt-4o", "Cloudflare/@cf/meta/llama-4-scout-17b-16e-instruct")
- The server dynamically resolves available providers at startup
- Providers that require authentication are excluded by default
- If a provider isn't available, the request will result in an error

## Troubleshooting

If you encounter issues, check the server logs for detailed error messages. You can increase the log level to `debug` for more verbose output:

```bash
llm4free-server --log-level debug
```

Common issues include:
- **Provider not found**: Verify the provider/model name format using the `/v1/models` endpoint
- **Network connectivity**: Ensure the server has internet access for provider APIs
- **Invalid request format**: Check request body against the OpenAI API specification
- **Authentication**: Note that API key is not required for this server, but some clients may expect one

For Docker-related issues, check container logs:
```bash
docker logs llm4free-api
docker-compose logs llm4free-api
```

*This documentation covers the comprehensive functionality of the [`llm4free.server`](../llm4free/server/__init__.py:1) module. For the most up-to-date information, refer to the source code and inline documentation.*
