# Changelog

## [Unreleased] - 2025-07-18

### Overview

This release introduces significant updates to AI provider models, dependency optimizations, enhanced provider functionality, and new model support for Scira and PerplexityLabs providers. The update focuses on expanding model availability across multiple AI providers, removing unnecessary dependencies, improving overall reliability, and enhancing provider refactoring. Key improvements include comprehensive model list updates for TogetherAI and TextPollinations providers, along with dependency cleanup to reduce package size and improve performance.

---

### Features

- **Expanded Model Support for TogetherAI Provider**
  - Added support for 70+ new AI models including:
    - DeepSeek R1 variants and distillations
    - Meta Llama 4 series (Maverick, Scout)
    - Qwen 2.5 and 3.x series models
    - Mistral Small 24B and enhanced variants
    - Specialized models like ChatGPT-5, MeowGPT-3.5
    - Community and enterprise models from various providers
  - **Enhanced OPENAI-compatible TogetherAI Provider**
    - Full OpenAI API compatibility with streaming support
    - Advanced token counting and usage tracking
    - Comprehensive error handling and retry mechanisms
    - Support for latest model releases and experimental variants

- **TextPollinations Provider Model Updates**
  - Reorganized model list with new additions:
    - Roblox-specific model variants (llama-fast-roblox, mistral-roblox)
    - Enhanced model ordering for better performance
    - Removed deprecated models (searchgpt)
    - Added specialized creative models (bidara, elixposearch, evil, etc.)
  - **Improved Model Management**
    - Better model validation and error handling
    - Consistent model naming conventions
    - Enhanced fallback mechanisms

- **New Model Support for Scira Providers**
  - Added support for the `kimi-k2-instruct` and `scira-kimi-k2` models in all Scira-related providers:
    - scira_search.py
    - scirachat.py
    - scira_chat.py
  - Ensures both forward and reverse mapping for these models, improving compatibility and user experience.

- **PerplexityLabs Provider Refactor**
  - Refactored the `PerplexityLabs` provider to use a polling-based connection approach instead of WebSockets.
  - Improved connection reliability, error handling, and session management.
  - Updated streaming and non-streaming response handling for better consistency and robustness.

---

### Improvements

- **Dependency Optimization**
  - Removed `websocket-client` dependency to reduce package size
  - Added `litproxy` for enhanced proxy support and meta-programming capabilities
  - Improved dependency resolution and conflict management

- **Provider Reliability**
  - Enhanced error handling across all updated providers
  - Better connection management and retry logic
  - Improved response parsing and validation

- **Model Availability**
  - Expanded model selection across multiple providers
  - Better model categorization and documentation
  - Enhanced model compatibility testing

- **Model Mapping Consistency**
  - Standardized model mapping logic across all Scira providers, ensuring aliases and reverse lookups are handled correctly.

- **Code Cleanup**
  - Removed unused imports and legacy WebSocket code from `PerplexityLabs`.
  - Improved docstrings and inline comments for maintainability.

---

### Fixes

- **Session and Authentication Handling**
  - Fixed issues with session initialization and authentication for PerplexityLabs, reducing connection errors and timeouts

---

### Dependencies

- **pyproject.toml**
  - Removed: `websocket-client` dependency
  - Added: `litproxy` for advanced proxy and metaclass support

---

### Documentation

- **Model Lists**
  - Updated available model documentation for TogetherAI and TextPollinations
  - Improved model categorization and descriptions
  - Better provider compatibility information

---

*Note: This release maintains backward compatibility while expanding functionality. All existing code should continue to work without modification.*

---

## [Unreleased] - 2025-07-10

### Overview

This update expands and standardizes the Scira model mappings across all Scira-related provider modules, ensuring support for the latest models and aliases. The changes improve compatibility with upstream provider definitions and enable access to new models for both chat and search functionalities.

---

### Features

- **Expanded Scira Model Support**
  - Added new models and aliases to the Scira model mapping, including:
    - `grok-4`, `qwen3-30b-a3b`, `deepseek-v3-0324`, and additional reverse mappings for Scira aliases.
  - Ensured all Scira-related providers (native, OpenAI-compatible, and search) expose a unified and current set of available models and aliases.

---

### Improvements

- **Model Mapping Consistency**
  - All Scira provider modules now share a unified and current model mapping, reducing confusion and improving maintainability.
  - Reverse mapping logic for aliases and special cases has been standardized.
  - Improved error messages and fallback logic for invalid model names.

- **Provider Model List Updates**
  - `Flowith.py`: Added `"gpt-4.1-nano"` to `AVAILABLE_MODELS`.
  - `Gemini.py` and `Bard.py`: Pruned unsupported/legacy Gemini models and updated aliasing for clarity and accuracy.

---

### Documentation

- **Inline Comments and Docstrings**
  - Updated and clarified docstrings and inline comments in all affected modules to reflect the expanded model support and mapping logic.

---

### Refactoring

- **Provider Interface Standardization**
  - Standardized model mapping and resolution logic across all Scira-related providers.
  - Removed redundant or inconsistent code paths for model selection and aliasing.

---

**Affected files:**
- `webscout/Provider/scira_chat.py`
- `webscout/Provider/OPENAI/scirachat.py`
- `webscout/Provider/AISEARCH/scira_search.py`
- `webscout/Provider/Flowith.py`
- `webscout/Provider/Gemini.py`
- `webscout/Bard.py`

## [Unreleased] - 2025-06-21

### Overview

This update introduces a new provider, utility enhancements, and improved stream handling for advanced AI workflows. The changes expand the provider ecosystem and make stream processing more flexible for developers.

---

### Features

- **MonoChat Provider**
  - Added a new provider module: `MonoChat` (`webscout/Provider/monochat.py`)
  - Registered `MonoChat` in the provider registry for seamless integration.

- **Stream Utility Enhancements**
  - Introduced a decorator version of `sanitize_stream` in `webscout/AIutel.py` for flexible and reusable stream sanitization.
  - Added aliase: `lit_streamer` for improved developer ergonomics.

---

### Improvements

- **Provider Registry**
  - Updated `webscout/Provider/__init__.py` to include `MonoChat` in the `__all__` list and provider imports.

- **Public Utility Imports**
  - Updated `webscout/__init__.py` to expose `sanitize_stream` and `lit_streamer` at the package level for easier access in downstream code.

---

### Documentation

- Added and updated docstrings for new and modified utility functions and provider modules.

---

## [Unreleased] - 2025-07-02

### Overview

This update focuses on Scira provider model mapping maintenance and compatibility improvements. It updates the model lists and aliasing logic for all Scira-related providers to match the latest API offerings, ensuring robust model resolution and consistent user experience across chat and search interfaces.

---

### Features

- **Provider Request Handling Improvements**
  - `LambdaChat.py` now uses improved browser-like headers, user-agent management, and multipart form data for enhanced compatibility and stability with upstream APIs.
- **Scira Model Mapping Overhaul**
  - Updated `MODEL_MAPPING`, `SCIRA_TO_MODEL`, and `AVAILABLE_MODELS` in all Scira providers:
    - `scira_chat.py`
    - `OPENAI/scirachat.py`
    - `AISEARCH/scira_search.py`
  - Added new models and aliases:
    - `scira-x-fast-mini` (grok-3-mini-fast)
    - `scira-x-fast` (grok-3-fast)
    - `scira-nano` (gpt-4.1-nano)
  - Ensured all reverse mappings and special cases are handled for robust model resolution.
  - Improved error messages and fallback logic for invalid model names.
---

### Fixes

- **Proxy Endpoint Update**
  - Updated the proxy source URL in `OPENAI/autoproxy.py` to use `https://proxies.typegpt.net/ips.txt` for more reliable proxy acquisition.
- **Model Alias Consistency**
  - Fixed inconsistencies in model aliasing and reverse mapping for Scira providers.
  - Ensured all supported models and aliases are available and correctly resolved.

---

### Refactoring

- **Provider Cleanup**
  - Removed deprecated provider modules:
    - `AI21.py`
    - `HuggingFaceChat.py`
  - Updated `Provider/__init__.py` to reflect these removals by cleaning up imports and the `__all__` list.

---

### Code Quality

- **Internal Consistency**
  - Ensured that only supported and maintained providers are exposed in the main provider package.

---

**Affected files:**
- `webscout/Provider/AI21.py` (deleted)
- `webscout/Provider/HuggingFaceChat.py` (deleted)
- LambdaChat.py (modified)
- autoproxy.py (modified)
- __init__.py (modified)
- `webscout/Provider/scira_chat.py` (modified)
- `webscout/Provider/OPENAI/scirachat.py` (modified)
- `webscout/Provider/AISEARCH/scira_search.py` (modified)
---

## [Unreleased] - 2025-07-02

### Overview

This update focuses on dependency management and provider model list maintenance. The "ollama" dependency has been removed, and related provider modules have been refactored for improved robustness and clarity. Model lists for Netwrck providers have been updated to reflect current API offerings.

---

### Fixes

- **Graceful Handling of Missing Dependencies**
  - OLLAMA.py now raises a clear `ImportError` if the `ollama` package is not installed, improving user feedback and robustness.

---

### Improvements

- **Provider Model List Updates**
  - Netwrck.py and netwrck.py:
    - Updated `AVAILABLE_MODELS` to remove deprecated models and add new ones.
    - Changed the default model to reflect current best practices and API support.

---

### Refactoring

- **Dependency Management**
  - Removed the "ollama" dependency from pyproject.toml to prevent unnecessary installation and potential conflicts.

---

### Dependencies

- **pyproject.toml**
  - "ollama" removed from dependencies.

---

## [Unreleased] - 2025-06-30

### Added
- **QodoAI Provider**: New AI provider integration supporting multiple models including GPT-4.1, GPT-4o, O3, O4-mini, Claude-4-sonnet, and Gemini-2.5-pro
  - OpenAI-compatible API interface for seamless integration
  - Support for both streaming and non-streaming responses
  - Dynamic session management and API key authentication
  - Web search and web fetch tools integration
- **Enhanced Provider Integration**: Updated `Provider/__init__.py` and `Provider/OPENAI/__init__.py` to include QodoAI
- **Improved Authentication**: Better error handling for invalid API keys across providers

### Changed
- Updated `.gitignore` to remove obsolete entries (`blackbox_private_key.pem`, `gpu.py`, `lol.py`)
- Enhanced OpenAI README documentation to include QodoAI provider usage examples

### Fixed
- Improved error handling in QodoAI provider for better user experience
- Better session management for API providers


## [Unreleased] - 2025-06-27

### Overview

This update introduces major improvements to Gemini and FreeAIChat provider support, expands model availability across ExaChat, DeepInfra, and GeminiProxy, and enhances the web search API with Bing integration. The release also removes legacy OpenAI-compatible FreeAIChat code, streamlines provider imports, and updates documentation for clarity and accuracy.

---

### Features

- **Expanded Gemini Model Support**
  - Added new Gemini models to ExaChat, GeminiProxy, and FreeGemini providers, including:
    - `gemini-2.5-flash-lite-preview-06-17`
    - `gemini-2.5-flash`
    - `gemini-2.5-pro`
  - Updated endpoints and model lists to reflect the latest Gemini releases.
  - **Affected files:**
    - `webscout/Provider/ExaChat.py`
    - `webscout/Provider/GeminiProxy.py`
    - `webscout/Provider/FreeGemini.py`

- **FreeAIChat Playground Integration**
  - Reimplemented the FreeAIChat provider to use the official FreeAIChat Playground API with automatic API key registration.
  - Added support for new and updated models, including `Deepseek R1 Latest`, `GPT 4o`, `O4 Mini`, `Grok 3`, `Gemini 2.5 Pro`, and more.
  - Improved error handling, Unicode decoding, and streaming support.
  - **Affected file:** `webscout/Provider/freeaichat.py`

- **Bing Search API Integration**
  - Added Bing as a supported engine in the unified web search API endpoint.
  - Enables text, news, image, and suggestion search types via Bing.
  - **Affected file:** `webscout/auth/routes.py`

---

### Improvements

- **Model List Updates**
  - Expanded and updated `AVAILABLE_MODELS` in ExaChat, DeepInfra, GeminiProxy, and FreeAIChat to include the latest models and aliases.
  - Improved model validation and error messages for unsupported models.
  - **Affected files:**
    - `webscout/Provider/ExaChat.py`
    - `webscout/Provider/Deepinfra.py`
    - `webscout/Provider/GeminiProxy.py`
    - `webscout/Provider/freeaichat.py`
    - `webscout/Provider/FreeGemini.py`

- **Provider Import Cleanup**
  - Removed legacy OpenAI-compatible FreeAIChat provider (`webscout/Provider/OPENAI/freeaichat.py`) and its import from `webscout/Provider/OPENAI/__init__.py`.
  - Ensured only the new native FreeAIChat provider is available.
  - **Affected files:**
    - `webscout/Provider/OPENAI/__init__.py`
    - `webscout/Provider/OPENAI/freeaichat.py` (removed)

- **Documentation and Usage Examples**
  - Updated OpenAI-compatible provider documentation to remove FreeAIChat from the provider list and usage examples.
  - Clarified available providers and improved example code for Gemini, ExaChat, and FreeAIChat.
  - **Affected file:** `webscout/Provider/OPENAI/README.md`

---

### Refactoring

- **API Key Handling**
  - FreeAIChat now automatically registers and fetches an API key if not provided, improving usability for new users.
  - Refactored internal logic for cleaner initialization and error reporting.

---

### Fixes

- **Endpoint and Model Consistency**
  - Fixed FreeGemini to use the correct Gemini 2.5 Flash endpoint.
  - Ensured all Gemini-related providers use up-to-date endpoints and model names.

---

### Removals

- **Legacy Code Cleanup**
  - Removed the OpenAI-compatible FreeAIChat provider and related import statements to avoid confusion and duplication.

---

### Documentation

- **README and Provider Docs**
  - Updated documentation to reflect new and removed providers, model lists, and usage patterns.
  - Improved clarity in provider tables and example code.

---

### Affected Files

- `webscout/Provider/ExaChat.py`
- `webscout/Provider/Deepinfra.py`
- `webscout/Provider/GeminiProxy.py`
- `webscout/Provider/FreeGemini.py`
- `webscout/Provider/freeaichat.py`
- `webscout/Provider/OPENAI/__init__.py`
- `webscout/Provider/OPENAI/freeaichat.py` (removed)
- `webscout/Provider/OPENAI/README.md`
- `webscout/auth/routes.py`

---

## [Unreleased] - 2025-06-26

### Overview

This update delivers a comprehensive refactor and expansion of model mapping logic across several AI provider modules, with a focus on the SciraAI and SciraChat providers. The changes standardize model aliasing, improve model resolution, and ensure consistency in available model listings. Additional improvements include enhanced error handling, updated test/demo code, and better maintainability for provider interfaces.

---

### Features

- **Robust Model Mapping and Aliasing**
  - Introduced or expanded `MODEL_MAPPING` and `SCIRA_TO_MODEL` dictionaries in SciraAI, SciraChat, and related providers for robust model aliasing and conversion.
  - Ensures seamless translation between user-facing model names and internal API model identifiers.
  - **Affected files:**
    - `webscout/Provider/AISEARCH/scira_search.py`
    - `webscout/Provider/OPENAI/scirachat.py`
    - `webscout/Provider/scira_chat.py`

- **Consistent Model Listings**
  - Updated `AVAILABLE_MODELS` lists in all affected providers to include all supported model names and aliases.
  - Commented out or removed unsupported models for clarity and accuracy.
  - **Affected files:**
    - `webscout/Provider/AISEARCH/scira_search.py`
    - `webscout/Provider/OPENAI/scirachat.py`
    - `webscout/Provider/scira_chat.py`
    - `webscout/Provider/TextPollinationsAI.py`
    - `webscout/Provider/typegpt.py`
    - `webscout/Provider/OPENAI/textpollinations.py`
    - `webscout/Provider/OPENAI/typegpt.py`

---

### Improvements

- **Enhanced Model Resolution and Error Handling**
  - Improved logic in `convert_model_name` and `_resolve_model` methods to handle aliases, fallbacks, and error cases more gracefully.
  - Ensures that invalid or unsupported model names are handled with clear error messages.

- **Test and Example Code Updates**
  - Updated `__main__` blocks in affected providers to iterate over all available models and print streaming response status, demonstrating the new model mapping logic.

- **Documentation and Comments**
  - Improved inline comments and docstrings to clarify model mapping, aliasing, and provider interface expectations.

---

### Refactoring

- **Provider Interface Standardization**
  - Standardized model mapping and resolution logic across all affected providers.
  - Removed redundant or inconsistent code paths for model selection and aliasing.

---

### Affected Files

- `webscout/Provider/AISEARCH/scira_search.py`
- `webscout/Provider/OPENAI/scirachat.py`
- `webscout/Provider/OPENAI/textpollinations.py`
- `webscout/Provider/OPENAI/typegpt.py`
- `webscout/Provider/TextPollinationsAI.py`
- `webscout/Provider/scira_chat.py`