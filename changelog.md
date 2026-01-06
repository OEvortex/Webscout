# Changelog

All notable changes to this project will be documented in this file.

## [2026.01.06] - 2026-01-06

### 🚮 Removed
- **remove**: Completely removed `webscout/Provider/AISEARCH/genspark_search.py` provider and all references to Genspark from the codebase
- **remove**: Updated `webscout/Provider/AISEARCH/__init__.py` to remove Genspark import and export
- **remove**: Updated documentation in `webscout/Provider/AISEARCH/README.md` and `Provider.md` to reflect removal of Genspark provider

### 🔧 Maintenance
- **refactor**: webscout/Provider/AISEARCH/monica_search.py - Simplified streaming content extraction by switching to an inline lambda for `sanitize_stream`'s `content_extractor` that returns `chunk["text"]` when present. Removed the now-unused `_extract_monica_content` method. Note: this change intentionally stops persisting `session_id` from stream payloads; reintroduce session handling if session persistence is required.
- **fix**: webscout/Provider/AISEARCH/webpilotai_search.py - Use `sanitize_stream`'s `content_extractor` for both streaming and non-streaming flows to parse JSON payloads and return the nested `content` (fallbacks to `text` and `data.delta.content` where present). This aligns behavior with `monica_search` and prevents empty or incomplete output when the service emits nested or delta-based content. Raw mode still returns unprocessed chunks.
- **fix**: webscout/Provider/AISEARCH/PERPLEXED_search.py - Fixed critical streaming issues and standardized with other providers:
  - Replaced manual JSON parsing with `sanitize_stream` using `line_delimiter="[/PERPLEXED-SEPARATOR]"` parameter
  - Fixed streaming generator that was not yielding chunks due to incorrect delimiter handling
  - Updated both streaming and non-streaming modes to use consistent `sanitize_stream` configuration
  - Improved content extraction logic to properly handle answer fields from JSON responses
  - Fixed `if __name__ == "__main__"` block to properly consume and display streaming responses
  - Now follows same pattern as webpilotai, miromind, and monica providers for consistency

## [2026.01.01] - 2026-01-01

### 🚮 Removed
- **remove**: Completely removed `google-generativeai` package dependency from pyproject.toml - package was not actually used in the codebase (geminiapi.py uses curl_cffi directly), removing it fixes Python 3.14 compatibility issues with pydantic-core
- **remove**: Completely removed `openai` package dependency from pyproject.toml - project now uses `curl_cffi` exclusively for HTTP requests, reducing dependencies and improving consistency
- **remove**: Completely removed `orjson` dependency from codebase (including imports, `HAS_ORJSON` flag, and pyproject.toml entry) for better compatibility and simpler dependencies
- **remove**: Completely removed `webscout/Provider/VercelAI.py` provider file and updated related imports and documentation
- **remove**: Removed `webscout/Provider/VercelAI.py` provider file and updated related imports and documentation
- **remove**: Completely removed `nodriver` package dependency from pyproject.toml - nodriver was not actively used in the codebase, only listed as a dependency
- **remove**: Replaced aiofiles usage with Python's built-in asyncio.to_thread for async file operations in TTS streaming, removing aiofiles dependency from pyproject.toml
- **remove**: Replaced cloudscraper usage with curl_cffi Session in LLMChat and LLMChatCo providers, removing cloudscraper dependency from pyproject.toml

### 🔧 Improved
- **refactor**: Made `lxml` dependency optional in pyproject.toml
  - Moved `lxml` to optional `parser` dependency group in pyproject.toml
  - Updated `webscout/search/base.py` to support lxml for HTML parsing
  - Updated `webscout/search/engines/duckduckgo/base.py` to use lxml for HTML parsing
- **refactor**: Migrated from `requests` to `curl_cffi` for HTTP requests in multiple files to improve browser fingerprinting and anti-detection capabilities
- **refactor**: Migrated `webscout/Provider/AISEARCH/iask_search.py` from `aiohttp` to `curl_cffi` for HTTP requests, while retaining `aiohttp` for WebSocket connections to improve browser fingerprinting and anti-detection capabilities

### 🐛 Fixed
- **fix**: Fixed ModuleNotFoundError for huggingface_hub in webscout versions > 2025.12.19 by implementing lazy imports in gguf.py
  - Replaced unconditional `from huggingface_hub import HfApi` with lazy import pattern
  - Added `_ensure_huggingface_hub()` function that imports HfApi only when GGUF features are used
  - Updated all HfApi usage in ModelConverter class to use lazy imports
  - This fixes import issues for users who only need chat/LLM provider features without GGUF conversion
  - Provides clear error message when GGUF features are used without huggingface_hub installed

### ✨ Added
- **feat**: Added new models to HadadXYZ providers: `"anthropic/claude-opus-4-5-20251101"`, `"anthropic/claude-sonnet-4-5-20250929"`, `"anthropic/claude-haiku-4-5-20251001/legacy"`, and `"google/gemini-3-pro-preview"` to both `webscout/Provider/HadadXYZ.py` and `webscout/Provider/OPENAI/hadadxyz.py`.

- **feat**: webscout/Provider/QwenLM.py - Added new models to this provider

- **feat**: Added `gpt-5.2` model to Toolbaz providers in both `webscout/Provider/toolbaz.py` and `webscout/Provider/OPENAI/toolbaz.py`

- **refactor**: Migrated `webscout/Provider/OPENAI/toolbaz.py` from `cloudscraper` to `curl_cffi` for consistent HTTP client implementation across providers

- **refactor**: Migrated `webscout/Provider/OPENAI/sonus.py` from `requests` to `curl_cffi` for improved browser emulation and consistency; updated form data handling from multipart `files` to standard `data` parameter

- **feat**: Added new OpenRouter provider in both `webscout/Provider/OpenRouter.py` and `webscout/Provider/OPENAI/openrouter.py` with dynamic model fetching and LitAgent browser fingerprinting

## [2025.12.21] - 2025-12-21

### 🐛 Fixed
- **fix**: Conducted an extensive codebase cleanup using Ruff, resolving over 200 linting issues and potential bugs.
- **fix**: Standardized error handling by replacing bare `except:` blocks with `except Exception:` or specific exception types across multiple modules (Bing search, GGUF converter, SwiftCLI, and various AI providers).
- **fix**: Resolved numerous `F821 Undefined name` and `F405` errors:
    - Restored missing `get_item` method in `YTdownloader.py`.
    - Defined missing variables (`result`, `content`, `tool_calls`) in `TextPollinationsAI.py` response processing.
    - Fixed missing `ic` imports from `litprinter` in multiple TTS providers (`MurfAI`, `OpenAI.fm`, `Parler`, `Qwen`, `Sherpa`, `FreeTTS`).
    - Fixed missing `exceptions` import in `FreeTTS`.
    - Resolved undefined `CLI` reference in SwiftCLI `Context` using `TYPE_CHECKING` and explicit imports.
    - Added missing type hint imports (`Optional`, `Any`, `Union`, `Generator`, `Response`) across 30+ AI provider modules including Cohere, Gemini, Groq, HuggingFace, and more.
    - Fixed undefined `LitAgent` reference in `GitToolkit/utils.py` and missing `Union` in `YTdownloader.py`.
    - Resolved `Response` naming conflict in `Ayle.py` by aliasing `curl_cffi` response.
- **fix**: Corrected syntax errors and corrupted logic blocks in `YTdownloader.py` and `iask_search.py`.
- **fix**: Improved project adherence to PEP 8:
    - Moved module-level imports to the top of files in `server` and `aihumanizer`.
    - Replaced incorrect type comparisons (e.g., `== bool`) with idiomatic `is bool`.
    - Split multiple statements on single lines (E701, E702) across the entire project for better readability.
- **refactor**: Replaced star imports (`from ... import *`) with explicit imports in `GitToolkit` and `samurai` provider to eliminate name shadowing and improve static analysis.
- **refactor**: Added dynamic model fetching to both DeepInfra providers (`webscout/Provider/Deepinfra.py`, `webscout/Provider/OPENAI/deepinfra.py`) following Groq provider pattern. Implemented `get_models()` and `update_available_models()` class methods that fetch from `https://api.deepinfra.com/v1/models` API endpoint with fallback to default models on failure. Providers now automatically update their available models list during initialization.
### 🚮 Removed
- **removed**: `yep.py` - Removed the YEPCHAT provider and related files.

## [2025.12.20] - 2025-12-20

### 📝 Documentation Updates
- **docs**: litprinter.md - Completely rewrote documentation to be comprehensive and consistent with other Webscout docs. Added detailed sections for IceCream debugging, Rich Console, Panels & Layouts, Traceback Enhancement, Themes & Styling, Advanced Usage, Integration with Webscout, API Reference, Dependencies, and Supported Python Versions. Enhanced with professional formatting, extensive code examples, and parameter tables.

### ✨ Added

- **feat**: webscout/Provider/Nvidia.py - New standalone Nvidia NIM provider with dynamic model fetching and advanced stream sanitization.
- **feat**: webscout/Provider/OPENAI/nvidia.py - New OpenAI-compatible Nvidia NIM provider with manual stream parsing.
- **feat**: webscout/Provider/HuggingFace.py - New standalone Hugging Face provider with dynamic model fetching and advanced stream sanitization.
- **feat**: webscout/Provider/OPENAI/huggingface.py - New OpenAI-compatible Hugging Face provider using HF Router with manual stream parsing.
- **feat**: webscout/Provider/ChatSandbox.py - Major update to ChatSandbox provider after reverse engineering. Expanded `AVAILABLE_MODELS` to include `deepseek-r1-full`, `gemini-thinking`, `llama`, and others.
- **feat**: webscout/Provider/OPENAI/chatsandbox.py - Updated OpenAI-compatible ChatSandbox provider with new model list and improved response extraction for reasoning and content.
- **feat**: Enhanced SwiftCLI with advanced argument and option validation including min/max length, regex patterns, and choices
- **feat**: Added JSON and YAML output formatters (`json_output`, `yaml_output`) for structured data output
- **feat**: Implemented command aliases system with `app.alias()` method for creating command shortcuts
- **feat**: Added command chaining support with `app.enable_chaining()` for complex workflows
- **feat**: Implemented shell completion script generation for bash, zsh, and fish shells via `generate_completion_script()`
- **feat**: Added mutually exclusive options support to prevent conflicting option combinations
- **feat**: Enhanced argument decorator with validation and mutually exclusive support
- **feat**: Added comprehensive validation functions in `utils/parsing.py` including `validate_argument` and `check_mutually_exclusive`
- **feat**: Updated CLI core to handle command aliases and validation in argument parsing
- **feat**: Added example script demonstrating all new features in `examples/advanced_features.py`
- **feat**: Updated documentation with new features and usage examples
- **feat**: Enhanced error handling with detailed validation error messages
- **feat**: Improved type safety with better runtime validation
- **feat**: webscout/Provider/TTI/together.py - Refactored TogetherImage provider to require a user-provided API key, removing the brittle auto-authentication logic. This aligns it with the TogetherAI chat providers.

### 🔧 Maintenance
- **chore**: Simplified optimizers module to include only the core coder optimizer, removing unused specialized optimizers to reduce complexity and maintenance overhead
- **chore**: Enhanced coder optimizer with improved system context and more detailed instructions for better code generation quality
- **feat**: webscout/Provider/TTI/pollinations.py - Expanded supported models list to include `flux-pro`, `flux-realism`, `flux-anime`, and `any-dark`.
- **feat**: `webscout/update_checker.py` - Major overhaul of the update system:
  - **Virtual Environment Awareness**: Intelligent detection of active `venv` and prioritized local package versioning.
  - **Pre-release Support**: Added capability to detect and recommend pre-release (beta/alpha) updates when running on a pre-release version.
  - **Development Version Detection**: Recognizes when the local version is ahead of PyPI (dev mode).
  - **Rich UI**: Integrated with `rich` for beautiful, high-fidelity update panels with vibrant colors and clear call-to-actions.
  - **Performance Optimization**: Implemented result caching (12 hours) and faster connection timeouts (3s) to ensure zero impact on script startup speed.
  - **Silent Mode**: Automatically disables check in non-TTY environments and respects `WEBSCOUT_NO_UPDATE` environment variable.
- **refactor**: `webscout/litagent/` - Major overhaul of the LitAgent module:
  - **Modernized Constants**: Updated browser and OS version ranges to reflect 2024/2025 standards (Chrome 131, Firefox 132, macOS 15.0, etc.).
  - **Enhanced Logic**: Improved user agent generation for diverse device types including Smart TVs, Gaming Consoles, and Wearables.
  - **Robust State Management**: Added internal pools for agents and IPs, with automatic background refresh capabilities.
  - **Thread Safety**: Implemented `RLock` support for multi-threaded environments.
  - **Fingerprinting**: Added support for `sec-ch-ua` headers and realistic browser fingerprints.
  - **Documentation**: Moved module documentation to `docs/litagent.md` and integrated it into the central hub.

### 🛠️ Improved
- **refactor**: webscout/Provider/TTI/ - Cleaned up the TTI module by removing 8 non-functional or login-required providers (`AIArta`, `BingImageAI`, `GPT1Image`, `ImagenAI`, `InfipAI`, `MonoChatAI`, `PiclumenAI`, `PixelMuse`).
- **refactor**: webscout/client.py - Updated unified client to support authenticated TTI providers in auto-failover mode when an API key is provided.
- **docs**: webscout/Provider/TTI/README.md - Updated documentation to reflect the current set of 5 functional TTI providers.
- **refactor**: `webscout/Provider/AISEARCH/` - Standardized `raw` parameter handling across all providers (Perplexity, Genspark, IAsk, Monica, PERPLEXED, webpilotai). Raw mode now returns/yields unprocessed strings/lines.
- **refactor**: `webscout/Provider/AISEARCH/` - Replaced manual SSE parsing with `sanitize_stream` using `extract_regexes` for robust JSON payload extraction in Perplexity, Genspark, and webpilotai.
- **refactor**: `webscout/Provider/AISEARCH/` - Standardized internal state tracking by renaming `last_SearchResponse` to `last_response` across all providers for better consistency.
- **fix**: `webscout/Provider/AISEARCH/webpilotai_search.py` - Fixed critical issue where search results were empty due to incorrect content accumulation logic; now correctly handles delta-based streaming.
- **fix**: `webscout/Provider/AISEARCH/iask_search.py` - Improved raw mode output to yield raw strings instead of dictionaries for better consistency with other providers.
- **refactor**: `webscout/Provider/AISEARCH/` - Enhanced `sanitize_stream` configuration with explicit encoding, buffer handling, and custom `content_extractor` functions to maintain provider-specific metadata (sources, status updates) during streaming.

### 🛠️ Improved
- **docs**: docs/cli.md - Updated CLI documentation to reflect all available commands, options, and examples based on actual implementation in webscout/cli.py.
- **docs**: README.md - Enhanced CLI section with comprehensive command examples and search provider information.
- **docs**: docs/openai-api-server.md - Updated documentation to reflect actual server implementation with Docker, configuration, and API endpoint details.
- **docs**: docs/client.md - Updated to emphasize client as Python-based API using models in OpenAI format, with relationship to server API clarified.

### ✨ Added
- **feat**: webscout/Provider/TTS/sherpa.py - New SherpaTTS provider using Next-gen Kaldi (Sherpa-ONNX) HF Space API, supporting 50+ languages and multiple ONNX models.
- **feat**: webscout/Provider/TTS/qwen.py - New Qwen3-TTS provider reverse engineered from Hugging Face Space demo, supporting 40+ high-quality voices and automatic language detection.
- **feat**: webscout/Provider/TTS/deepgram.py - Updated to support Aura-2 next-gen voices and latest API endpoint.
- **feat**: webscout/Provider/TTS/elevenlabs.py - Added support for ElevenLabs API keys.
- **feat**: webscout/Provider/TTI/miragic.py - New MiragicAI TTI provider reverse engineered from Hugging Face Space, supporting 'flux', 'turbo', and 'gptimage' models with streaming support.
- **feat**: webscout/server/routes.py - Added `/monitor/health` endpoint for Docker health checks, returning service status and version information.

### 🛠️ Improved
- **fix**: webscout/Provider/TTS/freetts.py - Fixed 404 error by updating to the latest synthesis API and polling mechanism.
- **fix**: webscout/Provider/TTS/parler.py - Switched to manual Gradio polling for improved reliability and timeout handling.
- **removed**: webscout/Provider/TTS/gesserit.py - Removed dead TikTok TTS provider.
- **refactor**: webscout/Provider/TTS/__init__.py - Added QwenTTS and SherpaTTS to the exported TTS providers.
- **refactor**: webscout/Provider/OPENAI/__init__.py - Added LLMChat to the list of exported OpenAI-compatible providers.
- **refactor**: webscout/Provider/OPENAI/e2b.py - Removed all unwanted `print` statements and ANSI escape codes to make the provider fully silent.
- **refactor**: webscout/Provider/TTS/ - Updated all TTS providers to use `ic` from litprinter instead of `print` for debugging, following the pattern established in deepgram.py:
  - Updated `murfai.py`, `openai_fm.py`, `parler.py`, `qwen.py`, `sherpa.py`, `streamElements.py`, `base.py`, `freetts.py`, `speechma.py`
  - All debug statements now use `ic.configureOutput(prefix='DEBUG| '); ic(f"Debug message")` pattern
- **refactor**: Docker configuration files for better dynamic configuration support:
  - Updated `.dockerignore` to properly exclude documentation while keeping essential files
  - Enhanced `docker-compose.yml` with accurate environment variable documentation
  - Improved `docker-compose.no-auth.yml` to reflect actual server capabilities
  - Updated `Dockerfile` with proper health check endpoint and dynamic configuration defaults
  - Improved `docs/DOCKER.md` documentation with accurate environment variable information

### 🚮 Removed
- **removed**: `gradio_client` dependency from pyproject.toml as it's no longer needed.
- **removed**: `gemini-2.0-flash` from Ayle provider model lists (`webscout/Provider/Ayle.py`, `webscout/Provider/OPENAI/ayle.py`).
- **removed**: webscout/Provider/AISEARCH/stellar_search.py - Removed dead Stellar AI search provider that was causing import errors and service unavailability.

### 🐛 Fixed
- **fix**: webscout/Provider/meta.py - Fixed HTTP/2 stream closure errors (curl error 92) by implementing robust retry mechanism with exponential backoff using AIutel retry decorator
- **fix**: webscout/Provider/meta.py - Added HTTP/1.1 fallback via requests library when HTTP/2 streams fail, ensuring compatibility with problematic networks
- **fix**: webscout/Provider/meta.py - Improved cookie extraction with retry logic, fallback to browser cookies, and better error handling for region-blocked sites
- **fix**: webscout/Provider/meta.py - Added `skip_init` parameter for offline testing and development without requiring live cookie fetching
- **fix**: webscout/Provider/meta.py - Enhanced streaming error recovery to gracefully handle connection interruptions during response iteration
- **fix**: webscout/Provider/meta.py - Improved main module error handling with helpful guidance for network issues and testing modes
- **test**: Added comprehensive unit tests in `tests/test_meta_http2.py` for HTTP/2 fallback functionality and retry mechanisms
- **fix**: webscout/Provider/oivscode.py - Fixed type annotation bugs by updating optional parameters to use `Optional[str]` type hints, correcting method calls, and adding proper string handling in `get_message()` method
- **fix**: webscout/Provider/oivscode.py - Removed unwanted print statements from `fetch_available_models()` method and updated its docstring to reflect that it no longer prints models
- **fix**: webscout/sanitize.py - Fixed import organization issues using `ruff check --fix` to properly sort and format imports according to project standards
- **fix**: webscout/scout - Fixed multiple critical bugs, removed direct BeautifulSoup references and updated BS4-compatible messaging across the scout component. (Applied ruff checks and whitespace fixes)
- **fix**: webscout/scout/core/scout.py - Resolved `TypeError` in `extract_metadata` and standardized `find` return types.
- **fix**: webscout/scout/core/crawler.py - Improved domain validation security, fixed overly aggressive URL normalization, and corrected parser selection logic.
- **fix**: webscout/scout/element.py - Fixed class matching logic and self-closing tag rendering in `prettify`.
- **fix**: webscout/scout/parsers/lxml_parser.py - Implemented XML namespace stripping for cleaner tag names.
- **fix**: webscout/Provider/QwenLM.py - Fixed multiple critical bugs including syntax errors, indentation issues, and formatting problems. Applied ruff check fixes to resolve blank lines with whitespace, trailing whitespace, and proper docstring formatting.

## [2025.12.19] - 2025-12-19

### ✨ Added
  - **feat**: webscout/client.py - Enhanced unified Client interface for AI providers:
  - `client.chat.completions.create()` - OpenAI-compatible chat completions
  - `client.images.generate()` / `client.images.create()` - Unified image generation
  - **Intelligent Model Resolution**:
    - `model="auto"`: Automatically selects a random free provider and its default model
    - `model="ProviderName/model_name"`: Directly target a specific provider and model (e.g., `"Toolbaz/grok-4.1-fast"`)
    - `model="model_name"`: Automatically finds which provider supports the requested model
  - **Simplified Auth Detection**: Providers are now identified as "free" or "auth-required" based solely on the `required_auth` attribute
  - **Auto-failover**: Improved failover logic that intelligently adjusts model names across different providers
  - **Failover on Empty Response**: Added logic to detect empty or invalid non-streaming responses and automatically trigger failover to alternative providers.
  - Dynamic discovery for all 39+ chat and 13+ image providers
  - Support for custom `exclude` and `exclude_images` lists
      - **Fuzzy Model Matching**: Automatically finds the closest matching model name across all providers (both chat and TTI) if an exact match is not found (e.g., `model="grok-4.1-fst"` matches `"grok-4.1-fast"` and `model="fluux"` matches `"flux"`). Uses `difflib` with a 0.6 confidence cutoff.
      - Added `last_provider` property to track successful provider/model pairs
    - Cleaned up internal implementation and removed redundant debug prints
  - **feat**: webscout/Provider/OPENAI/typliai.py - New OpenAI-compatible TypliAI provider with streaming and non-streaming support for GPT-4.1, GPT-5, Gemini 2.5, Claude 4.5, and Grok 4 models.
  - **feat**: webscout/Provider/OPENAI/easemate.py - New OpenAI-compatible Easemate provider.
  - **feat**: webscout/Provider/OPENAI/freeassist.py - New OpenAI-compatible FreeAssist provider.
  
  ### 🔧 Improved
  - **refactor**: webscout/client.py - Robust model discovery logic that safely handles class attributes, instance properties (including `@property`), and `.models.list()` methods during model resolution and fuzzy matching.
  - **refactor**: webscout/Provider/Sambanova.py - Major refactor to align with TextPollinationsAI pattern:  - Implemented `sanitize_stream` for robust SSE parsing.
  - Added support for tools and tool calling via `tools` and `tool_choice`.
  - Added dynamic model fetching with `update_available_models`.
  - Integrated `LitAgent` for dynamic browser fingerprinting.

## [2025.12.18] - 2025-12-18

### 🚮 Removed
- **removed**: webscout/Provider/Perplexitylabs.py - Removed PerplexityLabs provider file.
- **removed**: PerplexityLabs entry from Provider.md documentation and statistics.
- **removed**: References to PerplexityLabs from webscout/Provider/__init__.py.
- **removed**: webscout/Provider/TeachAnything.py - Removed TeachAnything provider file.
- **removed**: TeachAnything entry from Provider.md documentation and statistics.
- **removed**: References to TeachAnything from webscout/Provider/__init__.py.
- **removed**: webscout/Provider/GeminiProxy.py - Removed GeminiProxy provider file.
- **removed**: GeminiProxy entry from Provider.md documentation and statistics.
- **removed**: References to GeminiProxy from webscout/Provider/__init__.py.

### 🛠️ Fixed
- **fix**: webscout/Provider/OPENAI/ - Fixed "Accept-Encoding" issue in multiple providers (`K2Think`, `AkashGPT`, `LLMChatCo`, `Yep`, `Zenmux`, `DeepInfra`) that caused decompression errors and empty responses when using `requests` or `cloudscraper` libraries.
- **fix**: webscout/Provider/turboseek.py - Updated provider to handle new HTML-based raw stream response format and improved HTML-to-Markdown conversion.


## [2025.12.17] - 2025-12-17

### ✨ Added

### 🚮 Removed
- **removed**: webscout/Provider/Nemotron.py - Removed Nemotron provider as the file doesn't exist and was causing import errors
- **removed**: References to NEMOTRON from webscout/Provider/__init__.py
- **removed**: Nemotron entry from Provider.md documentation

- **feat**: webscout/Provider/OPENAI/gradient.py - New OpenAI-compatible Gradient Network provider for accessing distributed GPU clusters with models GPT OSS 120B and Qwen3 235B
- **feat**: webscout/Provider/OPENAI/gradient.py - Supports both streaming and non-streaming modes with thinking/reasoning capability
- **feat**: webscout/Provider/OPENAI/gradient.py - Auto-detection of cluster mode per model (nvidia for GPT OSS 120B, hybrid for Qwen3 235B)
- **feat**: webscout/Provider/freeassist.py - New OpenAI-compatible FreeAssist provider using FreeAssist.ai API with access to multiple AI models including gemini 2.5 flash and flash lite and GPT-5-nano and GPT-5-mini
- **feat**: webscout/Provider/OPENAI/sambanova.py - New OpenAI-compatible Sambanova provider supporting Llama 3.1/3.3, Qwen, and DeepSeek models with streaming capabilities
- **feat**: webscout/Provider/OPENAI/meta.py - New OpenAI-compatible Meta AI provider with web authentication, optional Facebook login, and streaming support

### 🔧 Improved

- **refactor**: webscout/Provider/Gradient.py - Major rewrite with correct headers matching actual API, proper SSE response parsing for content/reasoningContent
- **refactor**: webscout/Provider/Gradient.py - Now uses sanitize_stream with custom _gradient_extractor following the pattern of other providers
- **refactor**: webscout/Provider/Gradient.py - Added MODEL_CLUSTERS mapping for auto-detection of cluster mode (nvidia for GPT, hybrid for Qwen3)
- **refactor**: webscout/Provider/Gradient.py - Updated model names to use spaces (GPT OSS 120B, Qwen3 235B) matching API format
- **feat**: webscout/Provider/OPENAI/freeassist.py - Supports both streaming and non-streaming modes with proper SSE parsing
- **feat**: webscout/Provider/OPENAI/zenmux.py - Implemented dynamic model list fetching from `https://zenmux.ai/api/v1/models` API endpoint, making it fully compatible with Groq provider pattern
- **refactor**: webscout/Provider/TextPollinationsAI.py - Switched to requests library and implemented proper non-streaming support via `stream=False` to match API behavior
- **fix**: webscout/Provider/OPENAI/textpollinations.py - Fixed duplicate code blocks and syntax errors, ensuring proper class structure and dynamic model fetching

### 🚮 Removed
- **removed**: webscout/Provider/OPENAI/FreeGemini.py - Removed FreeGemini provider due to service deprecation
- **removed**: webscout/Provider/OpenGPT.py - Removed OpenGPT provider from the project

### 🔧 Maintenance
- **refactor**: webscout/Provider/OPENAI/DeepAI.py - Implemented dynamic model fetching using `get_models()` and `update_available_models()` class methods following Cerebras provider pattern
- **refactor**: webscout/Provider/OPENAI/textpollinations.py - Implemented dynamic model fetching using `get_models()` and `update_available_models()` class methods following Cerebras provider pattern
- **refactor**: webscout/Provider/TTI/together.py - Implemented dynamic model fetching using `get_models()` and `update_available_models()` class methods following Cerebras provider pattern
- **docs**: Updated provider documentation to reflect consistent dynamic model fetching implementation across providers

## [2025.12.16] - 2025-12-16

### ✨ Added

- **feat**: webscout/Provider/OPENAI/zenmux.py - Added `get_models()` and `update_available_models()` class methods for automatic model discovery and updating AVAILABLE_MODELS on initialization

#### GGUF Converter v2.0 Major Update
- **feat**: webscout/Extra/gguf.py - Upgraded to version 2.0.0 with latest llama.cpp features
- **feat**: Added new output types (`--outtype`): `f32`, `f16`, `bf16`, `q8_0`, `tq1_0`, `tq2_0`, `auto`
- **feat**: Added remote mode (`--remote`) for experimental tensor streaming without full model download
- **feat**: Added dry run mode (`--dry-run`) to preview split plans without writing files
- **feat**: Added vocab-only mode (`--vocab-only`) to extract just vocabulary without model weights
- **feat**: Added no-lazy mode (`--no-lazy`) to disable lazy evaluation for debugging
- **feat**: Added model name override (`--model-name`) for custom output naming
- **feat**: Added small first shard (`--small-first-shard`) for metadata-only first split file
- **feat**: Added new K-quant types: `q2_k_s`, `q4_k_l`, `q5_k_l`
- **feat**: Added ternary quantization: `tq1_0` (1-bit), `tq2_0` (2-bit) experimental
- **feat**: Added comprehensive IQ (importance-based) quantization methods:
  - 1-bit: `iq1_s`, `iq1_m`
  - 2-bit: `iq2_xxs`, `iq2_xs`, `iq2_s`, `iq2_m`
  - 3-bit: `iq3_xxs`, `iq3_xs`, `iq3_s`, `iq3_m`
  - 4-bit: `iq4_nl`, `iq4_xs`

#### GitToolkit Enhancements
- **feat**: webscout/Extra/GitToolkit/gitapi/search.py - New `GitSearch` class with methods for GitHub Search API: `search_repositories()`, `search_users()`, `search_topics()`, `search_commits()`, `search_issues()`, `search_labels()`
- **feat**: webscout/Extra/GitToolkit/gitapi/gist.py - New `Gist` class for public gist operations: `get()`, `list_public()`, `list_for_user()`, `get_commits()`, `get_forks()`, `get_revision()`, `get_comments()`
- **feat**: webscout/Extra/GitToolkit/gitapi/organization.py - New `Organization` class for org data: `get_info()`, `get_repos()`, `get_public_members()`, `get_events()`
- **feat**: webscout/Extra/GitToolkit/gitapi/trending.py - New `Trending` class for GitHub trending: `get_repositories()`, `get_developers()`
- **feat**: webscout/Extra/GitToolkit/gitapi/repository.py - Added 9 new methods: `get_readme()`, `get_license()`, `get_topics()`, `get_forks()`, `get_stargazers()`, `get_watchers()`, `compare()`, `get_events()`
- **feat**: webscout/Extra/GitToolkit/gitapi/user.py - Added 2 new methods: `get_social_accounts()`, `get_packages()`

#### YTToolkit Enhancements
- **feat**: webscout/Extra/YTToolkit/ytapi/suggestions.py - New `Suggestions` class for YouTube autocomplete: `autocomplete()`, `trending_searches()`
- **feat**: webscout/Extra/YTToolkit/ytapi/shorts.py - New `Shorts` class for YouTube Shorts: `is_short()`, `get_trending()`, `search()`
- **feat**: webscout/Extra/YTToolkit/ytapi/hashtag.py - New `Hashtag` class for hashtag videos: `get_videos()`, `get_metadata()`, `extract_from_text()`
- **feat**: webscout/Extra/YTToolkit/ytapi/captions.py - New `Captions` class for video transcripts: `get_available_languages()`, `get_transcript()`, `get_timed_transcript()`, `search_transcript()`
- **feat**: webscout/Extra/YTToolkit/ytapi/video.py - Added new properties/methods: `is_live`, `is_short`, `hashtags`, `get_related_videos()`, `get_chapters()`, `stream_comments()`
- **feat**: webscout/Extra/YTToolkit/ytapi/query.py - Added new search methods: `shorts()`, `live_streams()`, `videos_by_duration()`, `videos_by_upload_date()`
- **feat**: webscout/Extra/YTToolkit/ytapi/extras.py - Added new trending methods: `shorts_videos()`, `movies()`, `podcasts()`

### 🔧 Improved
- **refactor**: webscout/Extra/YTToolkit/transcriber.py - Rewrote YTTranscriber to use YouTube's InnerTube API for more reliable transcript fetching, replacing brittle HTML parsing with direct API calls
  - Uses `/youtubei/v1/player` endpoint for stable data extraction
  - Added better error handling for IP blocks, bot detection, and age-restricted videos
  - Fixed caption name parsing for new YouTube format (runs vs simpleText)
  - Removed problematic `&fmt=srv3` from caption URLs
  - Added fallback XML parsing for edge cases

### 🔧 Maintenance
- **refactor**: webscout/Extra/GitToolkit/gitapi/__init__.py - Updated exports to include new classes
- **refactor**: webscout/Extra/YTToolkit/ytapi/__init__.py - Updated exports to include new classes
- **docs**: webscout/Extra/GitToolkit/gitapi/README.md - Updated documentation with all new features and examples
- **docs**: webscout/Extra/YTToolkit/README.md - Updated documentation with all new features and examples
- **refactor**: webscout/Extra/gguf.py - Updated conversion logic to use dynamic outtype instead of hardcoded f16
- **refactor**: webscout/Extra/gguf.py - Improved split size validation to support K, M, G units matching llama.cpp
- **refactor**: webscout/Extra/gguf.py - Added outtype validation against VALID_OUTTYPES set
- **docs**: Moved webscout/Extra/gguf.md → docs/gguf.md for better documentation organization
- **docs**: docs/gguf.md - Complete rewrite for v2.0 with all new features, examples, and troubleshooting

### 🚮 Removed
- **removed**: webscout/Extra/autocoder/ - Completely removed AutoCoder package directory and all its files.
- **refactor**: webscout/AIutel.py - Removed AutoCoder import.
- **refactor**: webscout/Extra/__init__.py - Removed AutoCoder import.


## [2025.12.09] - 2025-12-09

### ✨ Added
- **feat**: pyproject.toml - Added `litprinter` dependency for improved logging functionality
- **feat**: webscout/Provider/OPENAI/utils.py - Added dict-like access methods (`__getitem__`, `__setitem__`, `keys`, `values`, `items`) to `ChatCompletionMessage` class for better compatibility
- **feat**: webscout/Provider/OPENAI/PI.py - Added missing `count_tokens` import for proper token counting functionality

### 🐛 Fixed
- **fix**: webscout/server/providers.py - Added `required_auth = False` filtering to only initialize OpenAI-compatible providers that don't require authentication, improving server startup and reducing provider count to 28 no-auth providers

### 🔧 Maintenance
- **refactor**: Replaced Litlogger with litprinter across entire codebase for consistent logging:
  - **refactor**: webscout/Extra/autocoder/autocoder.py - Updated logger initialization comment
  - **refactor**: webscout/Extra/tempmail/async_utils.py - Replaced standard logging with litprinter
  - **refactor**: webscout/Provider/OPENAI/K2Think.py - Replaced Litlogger imports with litprinter
  - **refactor**: webscout/Provider/OPENAI/base.py - Replaced Litlogger with litprinter for error logging
  - **refactor**: webscout/Provider/TTS/speechma.py - Replaced Litlogger with litprinter
  - **refactor**: webscout/Provider/meta.py - Removed unused logging import
  - **refactor**: webscout/__init__.py - Removed Litlogger import
  - **refactor**: webscout/conversation.py - Replaced logging with litprinter
  - **refactor**: webscout/search/base.py - Replaced logging with litprinter
  - **refactor**: webscout/search/engines/wikipedia.py - Replaced logging with litprinter
  - **refactor**: webscout/search/http_client.py - Replaced logging with litprinter
  - **refactor**: webscout/server/config.py - Replaced Litlogger with litprinter
  - **refactor**: webscout/server/providers.py - Replaced Litlogger with litprinter
  - **refactor**: webscout/server/request_processing.py - Replaced Litlogger with litprinter and added inline utility functions
  - **refactor**: webscout/server/routes.py - Replaced Litlogger with litprinter
  - **refactor**: webscout/server/server.py - Replaced Litlogger with litprinter
- **refactor**: webscout/search/engines/__init__.py - Changed from auto-discovery to static imports for better performance and reliability
- **refactor**: webscout/Provider/AISEARCH/__init__.py - Cleaned up import comments
- **refactor**: webscout/server/request_processing.py - Added inline implementations of `get_client_ip()`, `generate_request_id()`, and `log_api_request()` functions to replace dependency on simple_logger.py
- **refactor**: README.md - Removed reference to deprecated LitLogger
- **refactor**: lol.py - Updated example to use ChatGPT provider and added cprint import

### 🚮 Removed
- **removed**: AGENTS.md - Deleted unused documentation file
- **removed**: webscout/Litlogger/ - Completely removed Litlogger package directory and all its files (README.md, __init__.py, formats.py, handlers.py, levels.py, logger.py)
- **removed**: webscout/litprinter/__init__.py - Removed redundant wrapper file
- **removed**: webscout/server/simple_logger.py - Deleted file as functionality moved inline to request_processing.py

## [2025.12.03] - 2025-12-03

### ✨ Added
- **feat**: webscout/search/engines/__init__.py - Updated auto-discovery logic to register all search engine classes with `name` and `category` attributes, not just BaseSearchEngine subclasses
- **feat**: webscout/server/routes.py - Added new `/search/provider` endpoint that returns details about each search provider including name, supported categories, and parameters
- **feat**: webscout/models.py - Enhanced LLM models class with `providers()` and `provider()` methods that return detailed provider information including models, parameters, and metadata
- **feat**: webscout/models.py - Added TTI (Text-to-Image) models support with `_TTIModels` class including detailed provider information methods
- **feat**: added all engines to cli.py
- **feat**: cli.py - Added CLI commands for Bing search (text, images, news, suggestions)
- **feat**: cli.py - Added CLI commands for Yahoo search (text, images, videos, news, answers, maps, translate, suggestions, weather)
- **feat**: Algion.py - Implemented dynamic model loading from API without hardcoded defaults, ensuring AVAILABLE_MODELS is only populated if API fetch succeeds
- **feat**: Cerebras.py - Modified AVAILABLE_MODELS to use dynamic loading without defaults, requiring API key for model fetching
- **feat**: OPENAI/algion.py - Added OpenAI-compatible Algion provider with dynamic model loading
- **feat**: OPENAI/cerebras.py - Added OpenAI-compatible Cerebras provider with dynamic model loading
- **feat**: OPENAI/elmo.py - Added OpenAI-compatible Elmo provider
- **feat**: conversation.py - Added logging import for debug messages in file operations
- **feat**: conversation.py - Added __trim_chat_history private method for history length management

### 🐛 Fixed
- **fix**: webscout/server/routes.py - Fixed search engine method checking bug where it was looking for `hasattr(searcher, type)` instead of `hasattr(searcher, "run")`, preventing DuckDuckGo and other engines from working
- **fix**: webscout/server/routes.py - Fixed FastAPI UI documentation issue where search engines were listed multiple times by using `set()` to get unique engine names
- **fix**: webscout/search/engines/brave.py - Added `run` method to Brave search engine class for compatibility with search endpoint
- **fix**: webscout/search/engines/mojeek.py - Added `run` method to Mojeek search engine class for compatibility with search endpoint
- **fix**: webscout/search/engines/yandex.py - Added `run` method to Yandex search engine class for compatibility with search endpoint
- **fix**: webscout/search/engines/wikipedia.py - Added `run` method to Wikipedia search engine class for compatibility with search endpoint
- **fix**: webscout/models.py - Fixed `_LLMModels.summary()` method which was missing its return statement, causing it to return `None` instead of the expected dictionary with provider and model counts

### 🔧 Maintenance
- **refactor**: Added dynamic model fetching to OPENAI and GEMINIAPI providers similar to Algion provider, with get_models() classmethod that fetches available models from API
- **refactor**: Updated models.py to prioritize get_models() method over AVAILABLE_MODELS for dynamic model loading in provider discovery
- **refactor**: Added `name` and `category` attributes to all DuckDuckGo search engine classes (text, images, videos, news, suggestions, answers, maps, translate, weather)
- **refactor**: Added `name` and `category` attributes to Bing search engine classes (text, images, news, suggestions)
- **refactor**: Added `name` and `category` attributes to Yep search engine classes (text, images, suggestions)
- **refactor**: Updated webscout/search/engines/bing/__init__.py to import and expose Bing search engine classes
- **refactor**: Updated `/search` endpoint description to reflect support for all available search engines and search types
- **refactor**: prompt_manager.py - Removed unused imports, redundant code, and cleaned up class for clarity and minimalism
- **chore**: prompt_manager.py - Minor optimizations and code style improvements
- **refactor**: cli.py - Cleaned up incomplete command stubs and fixed inconsistencies in option decorators
- **removed**: cli.py - Removed unused imports and broken command implementations
- **cleanup**: Removed unused `schemas.py` file from server.
- **refactor**: Removed all imports and references to `HealthCheckResponse` and `ErrorResponse` from `routes.py` and `__init__.py`.
- **refactor**: Cleaned up unused imports (secrets, etc.) in `routes.py`.
- **refactor**: Updated `__init__.py` to only export actively used symbols and remove legacy schema references.
- **refactor**: Ensured all server modules only contain necessary code and imports, improving maintainability and clarity.
- **refactor**: conversation.py - Simplified Conversation class to use string-based chat history instead of message objects, removing tool handling, metadata, timestamps, and complex validation
- **refactor**: conversation.py - Updated history format to use "User : %(user)s\nLLM :%(llm)s" pattern for consistency
- **refactor**: conversation.py - Removed all tool-related methods (handle_tool_response, _parse_function_call, execute_function, get_tools_description, update_chat_history_with_tool)
- **refactor**: conversation.py - Streamlined file loading and history management to use simple string concatenation
- **refactor**: yep.py - Removed tool parameter and tool handling logic from YEPCHAT provider
- **refactor**: yep.py - Simplified ask method to directly update chat history without tool processing
- **refactor**: TeachAnything.py - No changes needed as it didn't use tool functionality

### 🚮 Removed
- **removed**: conversation.py - Removed Fn class, Message dataclass, FunctionCall, ToolDefinition, FunctionCallData TypedDicts
- **removed**: conversation.py - Removed add_message, validate_message, _append_to_file, _compress_history methods
- **removed**: conversation.py - Removed tool_history_format and related attributes
- **removed**: yep.py - Removed tool-related imports and examples from docstrings
- **removed**: AsyncProvider - Completely removed AsyncProvider class and all imports from provider files (Cohere.py, Groq.py, Koboldai.py, julius.py, HeckAI.py, ChatHub.py)
- **removed**: AsyncGROQ - Removed AsyncGROQ class from Groq.py that inherited from AsyncProvider
- **removed**: webscout/server/routes.py - Removed monitoring endpoints (`/monitor/requests`, `/monitor/stats`, `/monitor/health`) and related code from server
- **removed**: webscout/server/simple_logger.py - Removed unused monitoring methods (`get_recent_requests`, `get_stats`) from SimpleRequestLogger class


## [2025.12.01] - 2025-12-01
### ✨ Added
 - **feat**: sanitize.py - Added `output_formatter` parameter to `sanitize_stream()` for custom output transformation
 - **feat**: sanitize.py - Users can now define custom formatter functions to transform each output item into any desired structure before yielding

### 🚮 Removed
 - **removed**: sanitize.py - Removed built-in response formatters (`ResponseFormatter`, `OutputFormat`, `create_openai_response`, `create_openai_stream_chunk`, `create_anthropic_response`, `create_anthropic_stream_chunk`, `format_output`) in favor of user-defined `output_formatter` functions
 - **removed**: sanitize.py - Removed `output_format` and `format_options` parameters from `sanitize_stream()` - use `output_formatter` instead

### 📝 Documentation
 - **docs**: sanitize.md - Updated documentation with `output_formatter` parameter and usage examples
 - **docs**: sanitize.md - Removed references to removed built-in formatters

## [2025.11.30] - 2025-11-30

### 🔧 Maintenance
 - **refactor**: Added missing `# type: ignore` to imports for optional dependencies (trio, numpy, tiktoken, pandas) in multiple modules for better compatibility and linting
 - **refactor**: Improved type hints and error handling in `scout/core/crawler.py` and `scout/core/scout.py`
 - **refactor**: Updated `oivscode.py` to generate and use a unique ClientId (UUID) in headers
 - **refactor**: Updated CLI group import in `swiftcli/core/cli.py` to avoid circular dependency
 - **refactor**: Minor docstring and comment cleanups in AISEARCH providers
 - **chore**: Removed unfinished providers: `Aitopia.py`, `VercelAIGateway.py`, `puterjs.py`, `scira_search.py`, `hika_search.py` from Provider/UNFINISHED and Provider/AISEARCH

### 🐛 Fixed
 - **fix**: Fixed error handling in `sanitize.py` async stream processing (removed logger usage in extractor error branch)
 - **fix**: Fixed import and type hint issues in `duckduckgo/base.py`, `search/http_client.py`, `Provider/cerebras.py`, and others
 - **fix**: Fixed streaming output and test code in `genspark_search.py`, `PERPLEXED_search.py`, and `iask_search.py` for more robust CLI testing
 - **fix**: Fixed YahooSearch import for Dict type in `search/yahoo_main.py`

### 🚮 Removed
 - **removed**: Deleted unfinished provider files: `Aitopia.py`, `VercelAIGateway.py`, `puterjs.py`, `scira_search.py`, `hika_search.py` for codebase cleanup

### 🐛 Fixed
 - **fix**: TogetherAI.py - Updated API endpoint from `https://chat.together.ai/api/chat-completion` to `https://api.together.xyz/v1/chat/completions` for compatibility with the public Together API
 - **fix**: TogetherAI.py - Fixed payload parameters to use OpenAI-compatible format (`model`, `max_tokens`, `top_p` instead of `modelId`, `maxTokens`, `topP`)
 - **fix**: OPENAI/TogetherAI.py - Removed self-activation endpoint logic that auto-fetched API keys from external service

### ✨ Added
 - **feat**: TogetherAI.py - Implemented dynamic model loading from `https://api.together.xyz/v1/models` API, similar to Groq provider
 - **feat**: TogetherAI.py - Added `get_models()` and `update_available_models()` class methods for automatic model discovery
 - **feat**: OPENAI/TogetherAI.py - Added dynamic model loading support with automatic model list updates on initialization
 - **feat**: OPENAI/TogetherAI.py - Now requires user-provided API key via `api_key` parameter, following Groq provider pattern

### 🔧 Maintenance
 - **refactor**: TogetherAI.py - Changed `AVAILABLE_MODELS` from hardcoded dictionary to dynamically populated list
 - **refactor**: TogetherAI.py - Updated model validation to handle empty model lists gracefully when API fetch fails
 - **refactor**: OPENAI/TogetherAI.py - Removed `activation_endpoint` and `get_activation_key()` method for better security practices
 - **refactor**: OPENAI/TogetherAI.py - Updated `__init__` to accept `api_key` parameter and conditionally update models if key is provided

## [2025.11.21] - 2025-11-21

### 🐛 Fixed
 - **fix**: IBM.py - Fixed typo in `refresh_identity` method where `s-elf.headers` was incorrectly used instead of `self.headers`
 - **fix**: AIauto.py - Fixed critical bug where `chat` method could return a generator when `stream=False`, causing `AssertionError` in providers like AI4Chat
 - **fix**: AIauto.py - Added proper handling for providers that return generators even in non-streaming mode by consuming the generator to extract the return value

### ✨ Added
 - **feat**: AIauto.py - Enhanced provider failover mechanism to "peek" at the first chunk of streaming responses, allowing automatic failover to next provider if current one fails immediately
 - **feat**: AIauto.py - Split `chat` method into `_chat_stream` and `_chat_non_stream` helper methods for clearer separation of streaming vs non-streaming logic
 - **feat**: OPENAI/ibm.py - Added OpenAI-compatible IBM Granite provider in `webscout/Provider/OPENAI/` with support for `granite-chat` and `granite-search` models
 - **feat**: OPENAI/ibm.py - Implemented using `format_prompt()` and `count_tokens()` utilities from utils.py for proper message formatting and accurate token counting
 - **feat**: OPENAI/ibm.py - Manual SSE (Server-Sent Events) stream parsing without sanitize_stream dependency, consistent with other OPENAI providers

### 🔧 Maintenance
 - **refactor**: AIauto.py - Improved robustness of AUTO provider to work seamlessly with all providers in webscout.Provider package
 - **refactor**: AIauto.py - Added generator type checking and handling to prevent type mismatches between streaming and non-streaming responses

## [2025.11.20] - 2025-11-20

### 🐛 Fixed
 - **fix**: sanitize.py - Fixed critical async stream processing logic error where variable `idx` was used outside its conditional scope, causing potential `UnboundLocalError`
 - **fix**: sanitize.py - Fixed Python 3.9+ compatibility issue by replacing `Pattern` from typing with `re.Pattern` for proper isinstance() checks

### 🔧 Maintenance
 - **refactor**: sanitize.py - Reorganized imports for better structure (moved chain, functools, asyncio to top level)
 - **chore**: sanitize.py - Added `__all__` export list for explicit public API definition
 - **docs**: sanitize.py - Added comprehensive module docstring
 - **refactor**: sanitize.py - Updated all type hints to use modern syntax with `re.Pattern[str]`
 - **refactor**: Apriel.py - Simplified raw mode streaming logic for better performance

## [2025.11.19] - 2025-11-19

### 🔧 Maintenance
 - **chore**: Bard - added `gemini-3-pro` model with appropriate headers to `BardModel` enum
 - **GEMINI** - added `gemini-3-pro` model support in `GEMINI` class
 - **feat**: Updated search engines to use dataclass objects from results.py for better type safety and consistency
 - **refactor**: Updated all Providers to use `raw` flag of sanatize_stream for easy debugging
 - **removed**: Removed Cloudflare Provider

### 🐛 Fixed
 - **fix**: ChatGPT provider - Fixed OpenAI compatibility issues in `webscout/Provider/OPENAI/chatgpt.py` by updating streaming and non-streaming implementations to properly handle Server-Sent Events format and match OpenAI's response structure exactly
 - **fix**: ChatGPT provider - Enhanced error handling and parameter validation to follow OpenAI conventions
 - **fix**: AkashGPT provider - Fixed authentication issue in `webscout/Provider/akashgpt.py` by updating API key handling to use cookies for authentication

### ✨ Added
 - **feat**: ChatGPT provider - Added new models to AVAILABLE_MODELS including `gpt-5-1`, `gpt-5-1-instant`, `gpt-5-1-thinking`, `gpt-5`, `gpt-5-instant`, `gpt-5-thinking`
 - **feat**: New Provider: Algion with `gpt-5.1`and other models
## [2025.11.17] - 2025-11-17

### 🔧 Maintenance
 - **fix**: swiftcli - improved argument parsing: support `--key=value` and `-k=value` syntax; handle repeated flags/options (collected into lists)
 - **fix**: swiftcli - `convert_type` now handles boolean inputs and list-typed values robustly
 - **feat**: swiftcli - added support for option attributes: `count`, `multiple`, and `is_flag`; option callbacks supported; `choices` validation extended to multiple options
 - **fix**: swiftcli - option decorator uses a sentinel for unspecified defaults to avoid overriding function defaults with `None`
 - **feat**: swiftcli - CLI and `Group` now support the `@pass_context` decorator to inject `Context` and can run `async` coroutine commands
 - **fix**: swiftcli - help output deduplicates commands and displays aliases clearly; group help deduplicated and improved formatting
 - **test**: swiftcli - added comprehensive unit tests covering parsing, option handling (count/multiple/choices), `pass_context`, async behavior, group commands, and plugin manager lifecycle
 - **chore**: swiftcli - updated README with changelog, improved examples, and removed temporary debug/test helper files
 - **testing**: All swiftcli tests added in this change pass locally (14 tests total)

## [2025.11.16] - 2025-11-16
- **feat**: added `moonshotai/Kimi-K2-Thinking` and `MiniMaxAI/MiniMax-M2` models to DeepInfra provider AVAILABLE_MODELS in both `webscout/Provider/Deepinfra.py` and `webscout/Provider/OPENAI/deepinfra.py`
- **feat**: 

###  Maintenance
- **feat**: fixed formating issue in HeckAI replaced `strip_chars=" \n\r\t",`  with `strip_chars=""`
- **chore**: updated CHANGELOG.md to changelog.md in MANIFEST.in for consistency
- **chore**: updated release-with-changelog.yml to handle multiple version formats in changelog parsing
- **feat**: Updated changelog parsing to recognize multiple version formats (e.g., "vX.Y.Z", "X.Y.Z") for improved release automation.
- **feat**: updated `sanitize_stream` to support both `extract_regexes` and `content_extractor` at same time
- **chore**: updated `release-with-changelog.yml` to normalize version strings by stripping leading 'v' or 'V'
- **chore**: updated `sanitize_stream` docstring to clarify usage of `extract_regexes` and `content_extractor`
- **chore**: updated models list in textpollionations provider
- **chore**: replaced `anthropic:claude-3-5-haiku-20241022` with `anthropic:claude-haiku-4-5-20251001` in typefully provider 

### Added
- **feat**: added `anthropic:claude-haiku-4-5-20251001` to typefully provider AVAILABLE_MODELS
- **feat**: New IBM provider with `granite-search` and `granite-chat` models 

## [2025.11.06] - 2025-11-06

### 🔧 Maintenance
- **chore**: Remove GMI provider (a8928a0) — Cleaned up provider roster by removing GMI to simplify maintenance and reduce duplicate or deprecated provider support.

## [2025.10.22] - 2025-10-22

### ✨ Added
- **feat**: Add `claude-haiku-4.5` model to Flowith provider (3a80249) — Flowith now supports additional Claude variants for creative text generation.
- **feat**: Add `openai/gpt-oss-20b` and `openai/gpt-oss-120b` models to GMI provider (3a80249) — Added support for larger OSS GPT models via GMI.

### 🔧 Maintenance
- **refactor**: Change `DeepAI` `required_auth` to `True` (3a80249) — Ensure DeepAI provider requires authentication for API access.
- **chore**: Add import error handling for `OLLAMA` provider (3a80249) — Graceful degradation when optional dependencies are missing.
- **chore**: Remove deprecated `FalconH1` and `deepseek_assistant` providers (3a80249) — Reduced clutter and removed unsupported providers.
- **chore**: Update `OPENAI`, `flowith`, and `gmi` providers with new model lists and aliases (3a80249) — Keep model availability up-to-date and consistent.

## [2025.10.18] - 2025-10-18

### 🚀 Major Enhancements
- **🤖 AI Provider Expansion**: Integrated SciRA-AI and SciRA-Chat providers, adding robust model mapping and aliasing to unify behavior across providers.

### 📦 Package Structure
- **🛠️ Model Mapping System**: Introduced `MODEL_MAPPING` and `SCI_RA_TO_MODEL` dictionaries and updated `AVAILABLE_MODELS` lists to keep model names consistent and avoid duplication.

### ⚡ Improvements
- **🔄 Enhanced Model Resolution**: Improved `convert_model_name` and `_resolve_model` logic to better handle aliases, fallbacks, and unsupported names with clearer error messages.
- **🧪 Test and Example Updates**: Updated provider `__main__` blocks to list available models and print streaming behavior for easier local testing.
- **📝 Documentation**: Improved docstrings and comments clarifying model resolution and provider behavior.

### 🔧 Refactoring
- **⚙️ Provider Interface Standardization**: Refactored provider base classes and initialization logic to standardize how models are selected and aliases are resolved.

## [2025.10.17] - 2025-10-17

### ✨ Added
- **feat**: Add `sciRA-Coding` and `sciRA-Vision` providers (7e8f2a1)
- **feat**: Add `sciRA-Reasoning` and `sciRA-Analyze` providers (7e8f2a1)

### 🔧 Maintenance
- **chore**: Update provider initialization logic to more robustly support new sciRA families (7e8f2a1)
- **chore**: Add comprehensive model listings for newly added providers (7e8f2a1)

## [2025.10.16] - 2025-10-16

### ✨ Added
- **feat**: Add `sciRA-General` and `sciRA-Assistant` providers (9c4d1b3)
- **feat**: Add `sciRA-Research` and `sciRA-Learn` providers (9c4d1b3)

### 🔧 Maintenance
- **chore**: Refactor provider base classes for improved extensibility (9c4d1b3)
- **chore**: Add model validation logic to avoid exposing unsupported names (9c4d1b3)

## [2025.10.15] - 2025-10-15

### ✨ Added
- **feat**: Introduce SciRA provider framework and initial model mappings (5a2f8c7)

### 🔧 Maintenance
- **chore**: Set up SciRA provider infrastructure and basic authentication handling (5a2f8c7)

## [2025.10.10] - 2025-10-10

### ✨ Added
- **feat**: Add Flowith provider with multiple model support (b3d8a21)
- **feat**: Add GMI provider with advanced model options (b3d8a21)

### 🔧 Maintenance
- **chore**: Update provider documentation and add installation instructions for new providers (b3d8a21)

## [2025.10.05] - 2025-10-05

### ✨ Added
- **feat**: Initial release with core Webscout functionality (1a2b3c4) — Added web scraping, AI provider integration, and base CLI tooling.

### 🔧 Maintenance
- **chore**: Set up project structure, initial docs, and example workflows (1a2b3c4)

---

For more details, see the [documentation](docs/) or [GitHub repository](https://github.com/pyscout/Webscout).
---

For more details, see the [documentation](docs/) or [GitHub repository](https://github.com/pyscout/Webscout).
