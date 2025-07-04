# Changelog

## [Unreleased] - 2025-06-21

### Overview

This update introduces a new  provider, utility enhancements, and improved stream handling for advanced AI workflows. The changes expand the provider ecosystem and make stream processing more flexible for developers.

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
- `webscout/Provider/typegpt.py`

---

## [Unreleased] - 2025-06-25

### Overview

This update enhances the `sanitize_stream` utility in AIutel.py with powerful regex-based extraction and filtering capabilities, improving flexibility and control over streamed data processing.

---

### Features

- **Regex-Based Extraction and Skipping**
  - Added support for `extract_regexes` and `skip_regexes` parameters to `sanitize_stream` and all internal helpers.
  - Enables extraction of content using regex capturing groups and skipping of lines matching specified regex patterns.

---

### Improvements

- **Utility Enhancements**
  - Introduced the `_compile_regexes` helper to compile and validate regex patterns.
  - Propagated regex options through all relevant streaming and sanitization functions.
  - Improved docstrings and type hints for all updated methods, clarifying usage and expected behavior.

---

### Documentation

- **Docstring Updates**
  - Expanded and clarified documentation for `sanitize_stream` and related helpers, especially around new regex-based features.


## 8.3.3 – 2025-06-22

### Overview

This update introduces a new OpenAI-compatible provider, **MiniMax**, to the Webscout platform. The MiniMax provider enables seamless integration with the MiniMax-Reasoning-01 API, expanding the range of supported AI models and enhancing the flexibility of the OpenAI-compatible interface. This addition allows users to access MiniMax's reasoning capabilities through a familiar API, with both streaming and non-streaming support. The update also includes documentation improvements and necessary registration in provider lists.

---

### Features

- **New Provider: MiniMax (OpenAI-Compatible)**
  - Added `MiniMax` provider implementation in MiniMax.py and MiniMax.py.
    - Supports both streaming and non-streaming chat completions.
    - Follows the OpenAI-compatible interface for easy integration.
    - Handles reasoning content with `<think>` tags for enhanced interpretability.
    - Includes robust error handling and token counting for usage reporting.
    - Example usage and API details are provided in the code and documentation.
  - Motivation: Expands the set of available AI providers, giving users access to MiniMax's unique reasoning model via a standardized interface.

---

### Improvements

- **Provider Registration**
  - Registered the new MiniMax provider in:
    - __init__.py
    - __init__.py
  - Ensures MiniMax is available for import and use throughout the Webscout ecosystem.

- **Documentation**
  - Updated README.md:
    - Added "MiniMax" to the list of available OpenAI-compatible providers.
    - Ensured consistency in provider documentation and usage examples.

---

### Affected Files

- MiniMax.py (new)
- MiniMax.py (new)
- __init__.py (modified)
- __init__.py (modified)
- README.md (modified)

---

## 8.3.3 - 2025-06-21

### Overview

This release introduces **comprehensive support for raw streaming output** across all major AI provider modules in the `webscout.Provider` package. The update standardizes the `raw` parameter for both streaming and non-streaming chat/ask methods, enabling direct access to unprocessed API responses. This is a major refactor aimed at improving flexibility for advanced users, tool developers, and those integrating with custom frontends or pipelines. Additionally, several bug fixes, documentation improvements, and minor enhancements are included.

---

### Features

- **Raw Streaming Output Support**
  - All provider modules now support a `raw` parameter in their `ask` and `chat` methods.
  - When `raw=True`, methods yield or return the raw response chunks as received from the API, bypassing internal formatting, aggregation, or post-processing.
  - This enables advanced use cases such as custom streaming UIs, debugging, and integration with external tools.
  - **Affected files:**  
    - ExaChat.py
    - HeckAI.py
    - Jadve.py
    - Nemotron.py
    - Netwrck.py
    - OpenGPT.py
    - PI.py
    - StandardInput.py
    - TeachAnything.py
    - TextPollinationsAI.py
    - TogetherAI.py
    - Venice.py
    - VercelAI.py
    - WiseCat.py
    - WrDoChat.py
    - WritingMate.py
    - granite.py
    - koala.py
    - learnfastai.py
    - llmchat.py
    - llmchatco.py
    - multichat.py
    - scira_chat.py
    - scnet.py
    - searchchat.py
    - sonus.py
    - toolbaz.py
    - turboseek.py
    - typefully.py
    - typegpt.py
    - uncovr.py
    - x0gpt.py
    - yep.py

- **Enhancements to `sanitize_stream` Utility**
  - The `sanitize_stream` function in AIutel.py now supports a `raw` mode, yielding each chunk as received without splitting or joining.
  - This change underpins the new raw streaming support in all providers.

- **Proxy System Improvements**
  - Major update to autoproxy.py:
    - Adds static proxy lists (Webshare, NordVPN) and prioritizes Webshare proxies.
    - New helpers: `proxy()`, `patch()`, `use_proxy()`, `proxyify()`, `list_proxies()`, `test_all_proxies()`, `current_proxy()`.
    - Improved documentation and context manager for global proxy patching.

- **LitAgent Fingerprint Generation**
  - `LitAgent.generate_fingerprint` is now a static method, improving usability and consistency.
  - Ensures consistent browser fingerprinting for anti-fingerprinting and API compatibility.

---

### Fixes

- **Consistent Raw Output Handling**
  - All providers now correctly aggregate and yield raw output in both streaming and non-streaming modes.
  - Fixes issues where some providers would ignore the `raw` flag or only partially support it.

- **Streaming Aggregation Bugs**
  - Several providers (e.g., Venice.py, Netwrck.py, multichat.py, llmchat.py, llmchatco.py, x0gpt.py) now properly aggregate and yield streaming output, both in raw and processed modes.

- **Extractor and Content Handling**
  - Improved extractor logic in providers such as scira_chat.py, granite.py, TextPollinationsAI.py, and yep.py to handle both raw and processed content, including tool calls and special tags.

- **Error Handling**
  - More robust error handling for HTTP/network errors, JSON decode errors, and streaming edge cases across all providers.

---

### Improvements

- **Documentation and Comments**
  - Enhanced docstrings and inline comments for all updated methods, especially around the new `raw` parameter and streaming logic.
  - Improved clarity in provider class docstrings and method signatures.

- **Test and Example Code**
  - Updated example/test code in provider `__main__` blocks to demonstrate raw streaming usage.

- **Code Consistency**
  - Standardized method signatures and return types for `ask` and `chat` methods across all providers.
  - Improved type hints for generator and union return types.

- **Performance**
  - More efficient streaming chunk handling in several providers, reducing memory usage and improving responsiveness for large outputs.

---

### Refactoring

- **Provider Interface Standardization**
  - All providers now follow a consistent interface for streaming, non-streaming, and raw output.
  - Redundant or inconsistent code paths removed.

- **Proxy and Fingerprint Refactor**
  - Centralized proxy and fingerprint logic for easier maintenance and extension.

---

### Dependencies

- **pyproject.toml**
  - Added `litproxy` to dependencies for improved proxy and metaclass support.

---

### Documentation

- **README.md**
  - Minor formatting fix for compatibility section.

---


## 8.3.3 (June 19, 2025)

### Overview

This update (Unreleased, June 19, 2025) introduces major enhancements to the LitAgent user agent generator, focusing on advanced device support, proxy management, agent history, blacklist/whitelist features, and improved documentation. The changes provide greater flexibility for web scraping, more realistic agent rotation, and easier integration for developers.

### Features

- **LitAgent: Wearable Device Support**

  - Added a new `wearable()` method to generate user agent strings for wearable devices (e.g., Apple Watch, Samsung, Fitbit, Garmin).
  - **Files:** `webscout/litagent/agent.py`, `webscout/litagent/Readme.md`
  - **Motivation:** Expands device coverage for more realistic scraping and testing.

- **LitAgent: Proxy Pool & Rotation**

  - Introduced `set_proxy_pool()` and `rotate_proxy()` methods to manage and rotate through a pool of proxies.
  - **Files:** `webscout/litagent/agent.py`, `webscout/litagent/Readme.md`
  - **Motivation:** Simplifies proxy management for distributed or stealthy scraping.

- **LitAgent: Blacklist/Whitelist Support**

  - Enhanced the `random()` method to support agent blacklisting and whitelisting.
  - Added `add_to_blacklist()` and `add_to_whitelist()` methods.
  - **Files:** `webscout/litagent/agent.py`
  - **Motivation:** Allows fine-grained control over which user agents are used.

- **LitAgent: Agent History Tracking**

  - Added `_add_to_history()` and `get_history()` methods to track the last 50 user agents served.
  - **Files:** `webscout/litagent/agent.py`
  - **Motivation:** Enables auditing and debugging of agent usage patterns.

- **LitAgent: Agent Validation**
  - Added `validate_agent()` method to check if a user agent string is realistic.
  - **Files:** `webscout/litagent/agent.py`
  - **Motivation:** Helps ensure only valid user agents are used in requests.

---

### Improvements

- **LitAgent: Enhanced Documentation**

  - Updated `Readme.md` with new usage examples for wearable agents, proxy pool/rotation, blacklist/whitelist, agent history, and validation.
  - Improved formatting, added new sections, and clarified advanced usage patterns.
  - **Files:** `webscout/litagent/Readme.md`
  - **Motivation:** Makes it easier for developers to discover and use new features.

- **LitAgent: Random Agent Selection Logic**
  - Improved the `random()` method to prioritize whitelist, exclude blacklisted agents, and fall back gracefully.
  - **Files:** `webscout/litagent/agent.py`
  - **Motivation:** Ensures robust and predictable agent selection.

---

### Refactoring

- **LitAgent: Code Organization**
  - Grouped new device, proxy, and agent management methods for clarity and maintainability.
  - **Files:** `webscout/litagent/agent.py`
  - **Motivation:** Prepares the codebase for future extensibility.

---

### Acceptance Criteria

- All new methods are covered in the updated documentation.
- New features are accessible via the LitAgent API and demonstrated in the `__main__` test block.
- No breaking changes to existing LitAgent usage.

---

## (June 18, 2025)

### Overview

This update introduces new providers, enhanced error handling, improved API documentation, and significant refactoring for reliability and maintainability. Deprecated modules and unused code have been removed, and several features have been added to expand model and provider support. The release focuses on robustness, extensibility, and a cleaner codebase.

### Features

- **autoproxy**: Added auto-retry functionality for proxy requests with fallback to improve reliability in network operations.
- **openai**: Introduced MonoChat provider with completions and chat functionality.
- **AIArta**:
  - Added `models` property for better model management.
  - Added Stellar search provider implementation.
  - Defined `AVAILABLE_MODELS` for TTI provider map discovery and updated auth file handling.
  - Updated image generation logic and model handling.
- **TTI**: Added InfipAI provider for image generation with multiple models.
- **Providers**: Added Friendli provider with chat completion functionality.
- **auth**:
  - Enhanced API routes with descriptions for improved documentation.
  - Added tags for chat completions and web search routes.

### Improvements & Refactoring

- **deepinfra**: Streamlined response handling and improved error management in the Completions class.
- **flowith**: Cleaned up imports and enhanced error handling for response compression.
- **swagger**: Enhanced custom Swagger UI with improved footer and styling.
- **auth**: Implemented lazy imports for server functions to avoid module execution issues.
- **auth**: Enhanced error handling with GitHub footer in responses.
- **api**: Implemented custom Swagger UI with footer and disabled default docs.
- **BingSearch**: Simplified executor usage in the `text` method.
- **sanitize_stream**: Enhanced to support additional data types and improved handling of various input formats.

### Fixes

- **auth**: Enhanced error handling for TTI provider initialization.

### Removals & Cleanup

- **TTI**: Removed FastFluxAI provider and updated documentation.
- **NLP modules**: Removed deprecated modules for language detection, named entity recognition, text normalization, text processing, sentiment analysis, stemming, part-of-speech tagging, and tokenization utilities.
- **infip**: Removed unused imports for cleaner code.
- **UI**: Removed deprecated UI JavaScript and Swagger UI template.

### Chore & Maintenance

- **gitignore**: Removed `server.py` from `.gitignore` and added `gpu.py`.

---

## 8.3.3 (June 18, 2025)

### Overview

This update introduces new providers, enhanced error handling, improved API documentation, and significant refactoring for reliability and maintainability. Deprecated modules and unused code have been removed, and several features have been added to expand model and provider support. The release focuses on robustness, extensibility, and a cleaner codebase.

### Features

- **autoproxy**: Added auto-retry functionality for proxy requests with fallback to improve reliability in network operations.
- **openai**: Introduced MonoChat provider with completions and chat functionality.
- **AIArta**:
  - Added `models` property for better model management.
  - Added Stellar search provider implementation.
  - Defined `AVAILABLE_MODELS` for TTI provider map discovery and updated auth file handling.
  - Updated image generation logic and model handling.
- **TTI**: Added InfipAI provider for image generation with multiple models.
- **Providers**: Added Friendli provider with chat completion functionality.
- **auth**:
  - Enhanced API routes with descriptions for improved documentation.
  - Added tags for chat completions and web search routes.

### Improvements & Refactoring

- **deepinfra**: Streamlined response handling and improved error management in the Completions class.
- **flowith**: Cleaned up imports and enhanced error handling for response compression.
- **swagger**: Enhanced custom Swagger UI with improved footer and styling.
- **auth**: Implemented lazy imports for server functions to avoid module execution issues.
- **auth**: Enhanced error handling with GitHub footer in responses.
- **api**: Implemented custom Swagger UI with footer and disabled default docs.
- **BingSearch**: Simplified executor usage in the `text` method.
- **sanitize_stream**: Enhanced to support additional data types and improved handling of various input formats.

### Fixes

- **auth**: Enhanced error handling for TTI provider initialization.

### Removals & Cleanup

- **TTI**: Removed FastFluxAI provider and updated documentation.
- **NLP modules**: Removed deprecated modules for language detection, named entity recognition, text normalization, text processing, sentiment analysis, stemming, part-of-speech tagging, and tokenization utilities.
- **infip**: Removed unused imports for cleaner code.
- **UI**: Removed deprecated UI JavaScript and Swagger UI template.

### Chore & Maintenance

- **gitignore**: Removed `server.py` from `.gitignore` and added `gpu.py`.

---

# WebScout Changelog

## Version 8.3.2 (June 10, 2025)

### 2025-06-10

- ✨ **Feature:** Implement automatic proxy injection for OpenAI-compatible providers.
  - Enables seamless proxy configuration for all OpenAI-compatible providers, improving connectivity and reliability in restricted environments.
- ✨ **Feature:** Add GeminiProxy, DeepSeekAssistant and TogetherAI providers with API integration.
  - Introduces new providers for GeminiProxy, DeepSeekAssistant and TogetherAI, expanding the range of supported AI backends.
- 🔄 **Refactor:** Rename GeminiProxyLegacy to GeminiProxy and remove backward compatibility code.
  - Simplifies provider naming and codebase by removing legacy compatibility layers.
- ✨ **Feature:** Add BingImageAI provider with image generation capabilities.
  - Expands TTI (text-to-image) support with new provider for Bing.
- 🛠️ **Improve:** Enhance error handling and logging in SpeechMaTTS class.
  - Improves robustness and debuggability of the SpeechMa TTS provider.
- 🛠️ **Improve:** Refactor GGUF utilities for repository creation, file upload, and cross-platform compatibility.
  - Adds enhanced console feedback, error handling, and hardware detection for GGUF model management.
- 🛠️ **Improve:** Update CLI parameter handling and add fallbacks for rich progress components.
  - Ensures better compatibility with older versions and improves user experience in the CLI.
- 🧹 **Cleanup:** Remove unused API keys, rate limits, and users data files; update .gitignore for new files.
- 💄 **UI:** Refactor UI components for improved readability, consistency, and modern appearance.
  - Updates text, layout, CSS, and JavaScript for a more professional and accessible user interface.
- ✨ **Feature:** Add theme toggle functionality and UI utilities for WebScout.
  - Implements light/dark theme toggle, persistent theme storage, and utility functions for enhanced UX.
- 🛠️ **Improve:** Refactor code structure for improved readability and maintainability.
- 📝 **Docs:** Update README with server command options and no-auth mode instructions.
- ✨ **Feature:** Add XenAI provider and integrate model handling with auto-fetch token functionality.
- ✨ **Feature:** Implement automatic token fetching and update model list in MCPCore provider.
- 🛠️ **Fix:** Improve version retrieval and update messages with ANSI color codes in update_checker.
- 🛠️ **Fix:** Update telegram_id field to use default_factory and add validation method in auth system.
- 🛠️ **Fix:** Remove legacy API server and improve modular server startup.
  - Deprecates old backend, clarifies documentation, and enhances maintainability for authentication and rate limiting.
- ✨ **Feature:** Enhance find and find_all methods in scout module with class filtering and error handling.
- ✨ **Feature:** Implement Bing search library and unified web search endpoint with multiple engines.
- ✨ **Feature:** Add FastAPI metadata environment variables for Docker deployments.
- 🐛 **Fix:** Correct image generation API bug by updating method call to provider.images.create().
- 🛠️ **Improve:** Enhance stream sanitization and input type handling for robust input processing.

## Version 8.3 (May 29, 2025)

### 2025-05-29

- ✨ **Feature:** Add PI.ai provider with streaming and voice capabilities.
  - Introduces a new provider supporting both streaming and voice output, expanding the range of available AI integrations.
- 🔄 **Update:** Update available models in ChatSandbox and DeepInfra providers.
  - Adds new and alternative models to provider lists for improved compatibility and broader testing coverage.
  - Removes deprecated provider to streamline codebase and reduce maintenance overhead.
- 🛠️ **Improve:** Enhance provider APIs with model updates and dynamic API key generation.
  - Enables dynamic API key generation for improved usability and broader model coverage.
  - Optimizes session handling and refines warnings and headers for consistency.
  - Uncomments model discovery utility for easier endpoint introspection.
- 🛡️ **Enhance:** Improve model availability validation in provider resolution logic.
  - Updates logic to retrieve AVAILABLE_MODELS from provider classes, supporting both property and attribute access.
  - Implements fallback mechanisms and robust error handling for model discovery.
- 🗜️ **Dependency:** Add Brotli compression library to dependencies.
  - Enables support for Brotli-compressed responses in API server and client.
- 🚀 **Feature:** Implement streaming decompression for various content encodings in API server.
  - Adds support for on-the-fly decompression of Brotli, gzip, and deflate-encoded responses.
- 🧹 **Cleanup:** Sanitize text output to remove control characters and null bytes.
  - Ensures all response text is cleaned for valid, printable characters, improving client compatibility.
- 🐛 **Fix:** Improve UTF-8 handling and JSON serialization in response processing and streaming.
  - Enhances robustness for non-ASCII characters and prevents malformed responses.
- ⏱️ **Feature:** Add timeout and proxy support to Completions classes.
  - Introduces optional `timeout` and `proxies` parameters to the `create` method in all Completions classes for better network control.
- 🤖 **Feature:** Add FalconH1 provider with completions support and update imports.
  - Expands model and provider support for OpenAI-compatible APIs.
- 🧪 **Enhance:** Add gpt-4.1-mini and google/gemini-2.5-flash-preview models with agent mode support.
  - Broadens available model options for users and developers.

## Version 8.2.9 (May 2025)

### 2025-05-24

- 🔄 **Update:** Unifies AI search response handling via SearchResponse
- Introduces a shared SearchResponse class to standardize AI search API responses, replacing multiple custom response wrappers across providers
- Updates all search providers to utilize this unified approach, improving consistency, maintainability, and type clarity for both streaming and non-streaming modes
- Also removes an obsolete script and adds a new TTS provider import
- feat(Qwen3): add Qwen3 provider implementation with streaming and non-streaming support
- 🔨 **Refactor:** Refactors crawl logic to yield pages in real time
- Improves tag removal and visible text extraction for more accurate results.
- Switches crawling method to yield each crawled page as soon as available, enabling real-time processing and reducing memory usage.
- Enhances robustness by handling empty page results gracefully.
- ✨ **Feature:** Enhance crawling capabilities with improved URL validation and content extraction
- Adds stricter URL validation to prevent invalid or unsupported URLs from being processed.
- Improves content extraction logic for more accurate and relevant page data.
- Updates crawler to better handle edge cases and malformed input, increasing reliability.

### 2025-05-24

- 🚀 **Major Enhancement:** Complete overhaul of packaging, installation, and API server architecture.
  - **Fixed UV Package Manager Support:** Resolved `uv run webscout` dependency issue by correcting `ticktoken` → `tiktoken` typo in `pyproject.toml`, enabling seamless UV integration.
  - **Modernized Python Packaging:** Removed legacy `setup.py` file and migrated to modern `pyproject.toml`-only configuration following PEP 517/518 standards.
  - **Enhanced Installation Methods:** Added comprehensive UV support with multiple installation options:
    - `uv tool install webscout` - Global tool installation
    - `uv run webscout --help` - Direct execution without installation
    - `uv run --extra api webscout-server` - API server with dependencies
    - Traditional pip installation remains fully supported
  - **Comprehensive README Update:** Added detailed installation guide covering UV, pip, Docker, and development setups with practical examples and troubleshooting.
  - **API Server Architecture Overhaul:** Complete rewrite of `webscout/Provider/OPENAI/api.py` with enterprise-grade improvements:
    - **Centralized Configuration Management:** New `ServerConfig` class for better configuration handling
    - **Enhanced Error Handling:** Custom `APIError` exception class with OpenAI-compatible error responses
    - **Structured Logging:** Comprehensive logging system with proper levels and formatting
    - **Modular Code Architecture:** Split monolithic functions into focused, reusable components
    - **Robust Provider Management:** Improved provider discovery with fallback mechanisms
    - **Request Tracking:** Added unique request IDs for better debugging and monitoring
    - **Performance Monitoring:** Request timing and performance metrics
    - **Better Exception Handlers:** Comprehensive handlers for validation, HTTP, and general exceptions
  - **Improved CLI Documentation:** Updated command examples to showcase new UV integration and simplified usage patterns.
  - **Build System Optimization:** Streamlined build process with modern tools, removing unnecessary legacy files and improving package distribution.
- 🛠️ **Refactor:** Refactors API server, improves docs & removes TTI READMEs
  - Overhauls the API server for better structure, logging, error handling, and configuration flexibility.
  - Adds multi-stage Dockerfile optimized for production and updates installation and CLI usage instructions in the documentation.
  - Removes numerous provider-specific TTI README files for consistency and cleanup.
  - Deletes legacy workflow and test configuration files no longer needed.
  - Enhances extensibility and user experience for both development and deployment.
- 🖼️ **Refactor:** Refactors TTI image providers to unified, modular API
  - Moves all TTI providers to a new, unified architecture with a modular interface for image generation.
  - Removes legacy, provider-specific synchronous implementations, replacing them with a standardized async-compatible provider base and shared upload logic.
  - Enhances extensibility, testability, and consistency across providers, and aligns API signatures and response formats with OpenAI conventions.
  - Cleans up the provider registry, updates documentation references, and simplifies the user-facing API for easier integration and future provider additions.

### 2025-05-23

- 🔄 **Update:** Unifies client imports, adds Claude models, updates APIs.
  - Switches all usage examples and client imports to use a unified client import path for consistency and easier maintenance.
  - Introduces new Claude models (`claude-sonnet-4`, `claude-opus-4-20250514`) to supported model lists and providers, improving model coverage.
  - Updates Samurai API endpoint and credentials to reflect latest configuration.
  - Removes outdated provider documentation and usage examples from the OpenAI-compatible provider README to reduce confusion and reflect current state.
  - Corrects available model listings for X0GPT and oivscode providers.
  - Standardizes all usage examples and imports to a single client import path for easier maintenance.
  - Cleans up outdated provider documentation and usage examples to reduce confusion.
  - Updates Samurai API endpoint and credentials, and corrects model listings for oivscode and X0GPT.

### 2025-05-20

- 🔧 **Refactor:** Removed logging statements from OPENAI provider API for cleaner output and simplified codebase.
- ✨ **Feature:** Implemented lightweight logging library with multiple handlers in new Litlogger module.
- 🔨 **Fix:** Removed duplicate 'litlogger' directory (case conflict with 'Litlogger').
- 🔄 **Update:** Refactored OPENAI API models to support multimodal message content (text and image parts) for better OpenAI compatibility.
- 🔧 **Refactor:** Standardized logger format parameter naming and enhanced error handling.
- 🐛 **Fix:** Improved chat completions request example in Swagger UI.
- 🔨 **Refactor:** Replaced LitLogger with lightweight custom logger implementation without external dependencies.
- ✨ **Feature:** Enhanced BlackboxAI session generation with optional email input and diverse name/domain lists for greater realism.
- ✨ **Feature:** Added Microsoft Copilot provider integration to OPENAI module.
  - Included Copilot in provider list.
  - Updated `webscout\Provider\OPENAI\__init__.py` for Copilot import.
  - Added `webscout\Provider\OPENAI\copilot.py` to support Microsoft Copilot as an OpenAI-compatible provider.

### 2025-05-19

- ✨ **Feature:** Added PuterJS provider for interacting with the Puter.js API, including temporary account creation and image support.
- ✨ **Feature:** Implemented oivscode provider for test API interactions with model selection and robust error handling.
- 🔄 **Update:** Updated Bard providerV with new model definitions and enhanced error handling in API requests.

### 2025-05-18

- ✨ **Feature:** Implemented API key generation using temporary email in TwoAI provider.
- 🔄 **Update:** Enhanced TwoAI provider with image support and updated model details.
- 🐛 **Fix:** Improved API error handling and JSON parsing, especially for malformed requests from clients like PowerShell.
- 📝 **Documentation:** Added detailed API documentation through /docs, /redoc, and /openapi.json endpoints.
- ➕ **Dependency:** Added zstandard library for improved data compression capabilities.
- 🔧 **Change:** Modified plugin storage to use temporary directory instead of user's home directory for cleaner environment.

## Version 8.2.8 (May 2025)

### 2025-05-18

- ✨ **Feature:** Added NEMOTRON as an OpenAI-compatible provider.
- 📝 **Documentation:** Updated documentation and imports for NEMOTRON provider.
- 🛠️ **Improve:** Refined conversation validation logic for improved streaming support and role normalization, enhancing reliability.
- 🔨 **Refactor:** Simplified TypefullyAI provider by removing excessive comments and redundant docstrings for conciseness and maintainability.
- 🔄 **Update:** Updated available model lists for relevant providers.
- 💄 **Style:** Adjusted output formatting for clearer feedback.

- ✨ **Feature:** Added new models to LLMChat provider: `llama-4-scout-17b-16e`, `mistral-small-3.1-24b`, and `gemma-3-12b-it`.
- 🔨 **Refactor:** Converted models classmethod to property with `.list()` for all OpenAI providers, improving interface consistency and model discovery.
- 🛠️ **Improve:** Enhanced Meta provider response handling to always yield the latest message.
- 🐛 **Fix:** Improved error handling during conversation loading.
- 🔧 **Feature:** Introduced new labeler configuration for GitHub Actions.
- ✨ **Feature:** Implemented Flowith provider with streaming support for Flowith API.
- ✨ **Feature:** Created Cloudflare provider for OpenAI-compatible API interactions.
- ✨ **Feature:** Developed ChatSandbox provider for OpenAI-compatible chat interactions.
- 🪵 **Improve:** Enhanced Flowith provider with detailed request and response logging.
- ✨ **Feature:** Added Samurai provider for custom API interactions with improved error handling and streaming support.
- ✨ **Feature:** Added OpenAI-compatible API server for unified model serving and integration.
- 📝 **Documentation:** Updated documentation to reflect new providers, API server, and usage examples.
- 🔄 **Update:** Updated model list for TextPollinationsAI provider: added `openai-roblox` and removed `llama-vision`.
- 🐛 **Fix:** Resolved issue in `LambdaChat` provider that caused duplicate responses by removing redundant `finalAnswer` handling.
- ✨ **Feature:** Added LMArena provider in webscout
- ✨ **Feature:** Added Sthir provider with text-to-speech functionality.
- 🔄 **Update:** Updated SpeechMa provider voices.
- 🛠️ **Fix:** Fixed and expands model support and refines BlackboxAI integration. Extensively updates model selection with new agent and OpenRouter models, improves model aliasing and user selection logic, and implements dynamic session and request generation to better emulate client behavior. Enhances error handling, adds vision model support, and refreshes API payloads and headers for improved compatibility and maintainability.

## Version 8.2.7 (May 2025)

### 2025-05-10

- 🔨 **Refactor:** Migrated project configuration from `setup.py` to `pyproject.toml` for modern Python packaging standards. (#OEvortex)
- 🐛 **Fix:** Resolved CLI entrypoint issue by correcting the function reference in package configuration. (#OEvortex)
- 🗑️ **Remove:** Removed legacy `setup.py` file after complete migration to `pyproject.toml`. (#OEvortex)
- ✨ **Improve:** Enhanced AUTO provider to automatically exclude providers requiring authentication tokens or cookies. (#OEvortex)
- 🔧 **Feature:** Added option to print successful provider name in AUTO provider for better debugging. (#OEvortex)
- ✨ **Feature:** Implemented OpenAI-compatible interface for TypefullyAI provider with streaming support and standardized prompt formatting. (#OEvortex)
- 🔄 **Update:** Refreshed model list for TextPollinationsAI provider with latest available models. (#OEvortex)
- 🔄 **Update:** Updates model mapping in SciraChat providers
- 🐛 **Fix:** Enhanced shell command handling with `!` prefix in autocoder: (#OEvortex)
  - Modified `_extract_code_blocks` to properly detect shell commands in code blocks
  - Added support for shell commands in triple backticks without language tag
  - Implemented Jupyter-style UI for shell command execution and output display
  - Fixed issue with `main` method not properly handling shell commands
  - Added support for multiple shell commands in a single code block
  - Enhanced error handling and display for shell commands
- 🔧 **Feature:** Added limit parameter to trending video methods and updated model mapping: (#OEvortex)
  - Introduced optional limit parameter to all trending video retrieval methods
  - Allows trending video results to be capped directly within method calls
  - Updated AI model mapping to include support for an additional model
  - Improved provider flexibility with enhanced model support

## Version 8.2.6 (May 2025)

### 2025-05-05

- ✨ **Feature:** Added new model support for `GizAI` provider with enhanced API error handling. (#OEvortex)
- 🔨 **Refactor:** Optimized response streaming in `ChatSandbox` and `TypliAI` providers for better performance. (#OEvortex)
- 📝 **Documentation:** Updated README with new examples for GGUF converter usage. (#OEvortex)

### 2025-05-04

- ✨ **Feature:** Implemented batch processing capability in `MultiChatAI` provider. (#OEvortex)
- 🔧 **Change:** Updated default timeout values across all providers for better reliability. (#OEvortex)
- 🐛 **Fix:** Resolved memory leak issue in `TwoAI` streaming implementation. (#OEvortex)

### 2025-05-03

- ✨ **Feature:** Added experimental support for `SonusAI` voice synthesis models. (#OEvortex)
- 🔨 **Refactor:** Cleaned up import statements in `ElectronHub` for better code organization. (#OEvortex)
- 📝 **Documentation:** Added troubleshooting section for GGUF converter in README. (#OEvortex)

## Version 8.2.5 (May 2025)

### 2025-05-02

- 🔧 **Change:** Removed `inferno` folder and made it a standalone package: `inferno-llm` (available via `pip install inferno-llm`). (#OEvortex)
- 🔧 **Change:** Removed `webscout/Local` module as it's now part of the standalone Inferno package. (#OEvortex)
- 📝 **Documentation:** Updated README to reflect Inferno is now a standalone package with links to GitHub and PyPI repositories. (#OEvortex)
- ✨ **Feature:** Implemented `GizAI` provider for API interaction and enhanced response handling. (#OEvortex)
- 📝 **Documentation:** Added detailed documentation for GGUF converter with comprehensive usage examples and features. (#OEvortex)
- ✨ **Feature:** Implemented Google and Yep search commands in CLI with configurable options for region, safesearch, and result filtering. (#OEvortex)
- 🔨 **Refactor:** Cleaned up message validation logic in conversation module for improved reliability. (#OEvortex)

### 2025-05-01

- ✨ **Feature:** Added `ChatSandbox` and `TypliAI` providers with enhanced API interaction capabilities. (#OEvortex)
- 📝 **Documentation:** Updated README to add `MultiChatAI`, `AI4Chat`, and `MCPCore` to available providers list. (#OEvortex)
- ✨ **Feature:** Updated `TwoAI` API endpoint and enhanced streaming response handling for better performance. (#OEvortex)
- 🔨 **Refactor:** Cleaned up import statements in `ElectronHub` and `Glider` files for improved code readability. (#OEvortex)
- 🔨 **Refactor:** Integrated `sanitize_stream` for improved response handling across multiple providers: (#OEvortex)
  - Added to `MultiChatAI` for processing raw responses
  - Updated `SciraAI` for both streaming and non-streaming responses with error handling
  - Implemented in `SCNet` for JSON extraction from streaming data
  - Enhanced `SearchChatAI` for efficient data processing
  - Integrated in `SonusAI` for better content extraction from responses
  - Refactored `Toolbaz` to use `sanitize_stream` for tag removal in streaming text
  - Updated `TurboSeek` for JSON object extraction
  - Implemented in `TypefullyAI` for improved content extraction from streaming responses
  - Enhanced `TypeGPT` for both streaming and non-streaming responses
  - Integrated in `UncovrAI` for better handling of streaming and non-streaming data

## Version 8.2.4 (May 2025)

### 2025-05-01

- ✨ **Feature:** Enhanced `AIutel.py` chunk processing with byte stream decoding and integrated `sanitize_stream` across multiple providers (`yep.py`, `x0gpt.py`, `WiseCat.py`, `WritingMate.py`, `Writecream.py`, `HeckAI.py`) for improved data handling and cleaner code. (#OEvortex)

### 2025-04-30

- ✨ **Feature:** Implemented `MCPCore` API client (`Provider/OPENAI/mcpcore.py`) with model support and cookie handling. (#OEvortex)

### 2025-04-29

- ✨ **Feature:** Updated available models list for `HeckAI` provider. (#OEvortex)
- ✨ **Feature:** Updated available models list for `DeepInfra` and `ElectronHub` providers, adding dynamic model fetching. (#OEvortex)

### 2025-04-27

- ✨ **Feature:** Implemented `Groq` client (`Provider/OPENAI/groq.py`) for chat completions, switching API usage and updating model handling. (#OEvortex)
- ✨ **Feature:** Implemented model fetching from Groq API, updated available models, and switched to `curl_cffi` for HTTP requests in `Groq` provider (`Provider/Groq.py`). (#OEvortex)
- 🔨 **Refactor:** Refactored `ChatGPTClone` to use `curl_cffi`, removed `ChatGPTES`, added `AI4Chat`, enhanced error handling, and updated headers/session initialization across providers. (#OEvortex)

### 2025-04-25

- ✨ **Feature:** Added GGUF RAM estimation utilities and `MultiChatAI` provider implementation with support for multiple endpoints and streaming. (#OEvortex)

### 2025-04-23

- 🔨 **Refactor:** Replaced `primp` library with `curl_cffi` for HTTP requests across the `webscout` package. (#OEvortex)

## Version 8.2.3 (23 April 2025)

### 2025-04-23

- ✨ **Feature:** Implemented base TTS provider with audio saving and streaming functionality (#OEvortex)
  - Added foundational TTS provider class
  - Enabled audio file saving and streaming support

### 2025-04-22

- ✨ **Feature:** Updated available models in Toolbaz provider (#OEvortex)

### 2025-04-21

- 🗑️ **Remove:** Removed unfinished E2B API and Emailnator implementations (now completed) (#OEvortex)

## Version 8.2.2 (20 April 2024)

### 2024-04-20

- ✨ **Feature:** Added new models to E2B provider (#OEvortex)

  - Added support for o4-mini, gpt-4o-mini, gpt-4-turbo models
  - Added support for Qwen2.5-Coder-32B-Instruct model
  - Added support for DeepSeek R1 model

- 🔧 **Fix:** Updated Dependabot reviewer username to OEvortex (#OEvortex)

- 🔧 **Fix:** Fixed issues in the inferno CLI module (#OEvortex)

### 2024-04-19

- ✨ **Feature:** Implemented Emailnator provider for TempMail and updated provider list (#OEvortex)
  - Added new temporary email provider
  - Updated provider listings to include the new service

## Version 8.2.1 (19 April 2024)

### 2024-04-19

- ✨ **Feature:** Added E2B provider to OPENAI directory (#OEvortex)
  - Implemented OpenAI-compatible interface for E2B API
  - Added support for various models including claude-3.5-sonnet
  - ~~Enabled both streaming and non-streaming completions~~
  - Included comprehensive error handling and response formatting

## Version 8.2 (18 April 2024)

### 2024-04-18

- ✨ **Feature:** Implemented webscout.Local module with command-line interface (#OEvortex)

  - Added cli.py for managing models, including commands to serve, pull, list, remove, and run models
  - Integrated model management and loading functionalities
  - Enhanced user interaction with rich console outputs and prompts

- ✨ **Feature:** Added configuration management for webscout.Local (#OEvortex)

  - Introduced config.py to handle application configuration
  - Implemented loading, saving, and accessing configuration values
  - Default configurations for models directory, API host, and port

- ✨ **Feature:** Created LLM interface for local model integration (#OEvortex)

  - Developed llm.py to interface with llama-cpp-python for model loading and completion generation
  - Added methods for creating completions and chat responses

- ✨ **Feature:** Implemented model management functionalities (#OEvortex)

  - Created model_manager.py for downloading, listing, and removing models
  - Integrated Hugging Face Hub for model downloads and file management

- ✨ **Feature:** Implemented OpenAI-compatible API server (#OEvortex)

  - Added server.py to create an OpenAI-compatible API using FastAPI
  - Implemented endpoints for model listing and chat/completion requests

- ✨ **Feature:** Added utility functions for webscout.Local (#OEvortex)

  - Introduced utils.py for various utility functions including duration parsing and image encoding/decoding

- ✨ **Feature:** Added Perplexity search provider and updated README with examples (#OEvortex)

- ✨ **Feature:** Added XAI model configuration and updated available models in ExaChat (#OEvortex)

- ✨ **Feature:** Added WritingMate provider and updated cleanup script to remove .pytest_cache (#OEvortex)

- ✨ **Feature:** Updated available models in SciraAI and SciraChat (#OEvortex)

- ✨ **Feature:** Integrated TextPollinations API and updated related models (#OEvortex)

### 2024-04-17

- ✨ **Feature:** Switched from OPKFC to ChatGPT and updated model to auto (#OEvortex)

- 🧹 **Cleanup:** Removed all compiled Python files (.pyc) from the **pycache** directories (#OEvortex)

  - Ensured a clean build environment and prevented potential issues with stale bytecode

- ✨ **Feature:** Added OPKFC as new provider (#OEvortex)

- ✨ **Feature:** Added scira-o4-mini model to available models in SciraChat and SciraAI (#OEvortex)

- ✨ **Feature:** Implemented UncovrAI API integration and updated related files (#OEvortex)

### 2024-04-16

- ✨ **Feature:** Updated endpoints and added new models for ExaChat, GithubChat, Glider, and YouChat (#OEvortex)

### 2024-04-15

- ✨ **Feature:** Added Toolbaz and SCNet API implementations (#OEvortex)

  - Updated **init**.py for new providers

- ✨ **Feature:** Implemented Writecream API integration and updated client initialization (#OEvortex)

- ✨ **Feature:** Added StandardInputAI and E2B API implementations (#OEvortex)
  - Implemented StandardInputAI class for interacting with the Standard Input chat API
  - Added E2B class for encapsulating the E2B API, supporting various models
  - Included methods for building request bodies, merging user messages, and generating system prompts
  - Enhanced error handling and response parsing for API requests

### 2024-04-14

- ✨ **Feature:** Enhanced setup.py with additional classifiers and keywords (#OEvortex)

## Version 8.1 (14 April 2024)

### 2024-04-14

- ✨ **Feature:** Added OpenAI-compatible interfaces for multiple providers, enabling standardized API access (#OEvortex)

  - Implemented OpenAI-compatible interfaces for DeepInfra, Glider, ChatGPTClone, X0GPT, WiseCat, Venice, ExaAI, TypeGPT, SciraChat, LLMChatCo, FreeAIChat, and YEPCHAT
  - Added comprehensive documentation with usage examples for all OpenAI-compatible providers
  - Created standardized response formats matching OpenAI's structure for better compatibility

- 🔧 **Fix:** Resolved minor bugs in native compatibility implementations (#OEvortex)

  - Enhanced error handling and response processing across multiple providers
  - Improved model validation and selection logic
  - Standardized timeout handling for better reliability

- 📝 **Documentation:** Added detailed README for OpenAI-compatible providers with examples and model listings (#OEvortex)
  - Created comprehensive provider-specific documentation
  - Added code examples for both streaming and non-streaming usage
  - Updated main README with information about dual compatibility options

## Version 8.0 (13 April 2024)

### 2024-04-13

- 🔼 **Version:** Updated version to 8.0 (#OEvortex)
- ✨ **Feature:** Added SciraAI search provider with streaming support, multiple models, and DeepSearch capabilities (#OEvortex)
- ✨ **Feature:** Introduced 'gemini-2.5-pro' model to GitHub Chat for advanced interactions (#OEvortex)
- ✨ **Feature:** Enhanced DeepInfra with configurable system prompts and updated model availability (#OEvortex)
- ✨ **Feature:** Improved model configurations for Hika, ExaAI, and Netwrck providers (#OEvortex)
- ✨ **Feature:** Added support for new providers: OpenGPT, WebpilotAI, Hika, ExaAI, LLMChatCo, and TypefullyAI (#OEvortex)
- 🗑️ **Remove:** Removed non-functional models from DeepInfra for a cleaner experience (#OEvortex)
- ✨ **Feature:** Enhanced video metadata extraction with additional properties for better insights in YTToolkit (#OEvortex)
- ✨ **Feature:** Added retry logic and Turnstile token handling to improve AI chat functionality (#OEvortex)
- 🔨 **Refactor:** Refactored URL handling and error management for more reliable operations (#OEvortex)
- 🔨 **Refactor:** Streamlined provider configurations and removed deprecated entries (#OEvortex)

## Version 7.9 (April 2024)

### 2024-04-09

- 🔼 **Version:** Updated version to 7.9 (#OEvortex)
- 🗑️ **Remove:** Removed Editee provider and updated imports (#OEvortex)
- ✨ **Feature:** Updated ElectronHub AVAILABLE_MODELS with new AI model entries (#OEvortex)
- ✨ **Feature:** Added Llama 4 Scout and Llama 4 Maverick to FreeAIChat AVAILABLE_MODELS (#OEvortex)
- ✨ **Feature:** Updated Gemini model aliases and removed deprecated entries (#OEvortex)

### 2025-04-08

- 💄 **Style:** Standardized formatting and indentation in system context prompts for optimizers (#OEvortex)
- ✨ **Feature:** Added informative error raising if litprinter is not installed (#OEvortex)

### 2025-04-06

- ✨ **Feature:** Added "qwen25-coder-32b-instruct" to LambdaChat AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Added cerebras models and updated gemini model list in ExaChat (#OEvortex)
- ✨ **Feature:** Updated UncovrAI AVAILABLE_MODELS and enhanced error handling in response parsing (#OEvortex)
- ✨ **Feature:** Updated TextPollinationsAI AVAILABLE_MODELS list with new models and improved descriptions (#OEvortex)
- ✨ **Feature:** Restored google gemma models to DeepInfra AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Updated GROQ AVAILABLE_MODELS list with new models and removed commented entries (#OEvortex)
- ✨ **Feature:** Added new models to DeepInfra AVAILABLE_MODELS list (#OEvortex)

### 2025-04-05

- 🗑️ **Remove:** Removed DARKAI provider and updated imports (#OEvortex)
- ✨ **Feature:** Added new models to FreeAIChat AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Implemented TempMail package for temporary email generation (#OEvortex)
- 📝 **Documentation:** Clarified fallback behavior for litprinter import (#OEvortex)
- 🔨 **Refactor:** Replaced bundled litprinter implementation with external package import (#OEvortex)
- 🐛 **Fix:** Updated import statements and removed redundant warnings for better clarity in traceback (#OEvortex)
- 📝 **Documentation:** Revamped README with enhanced introduction, features, and installation instructions (#OEvortex)
- 📝 **Documentation:** Enhanced legal notice with clearer disclaimers and updated licensing terms (#OEvortex)
- 📝 **Documentation:** Updated changelog.md with a professional and modern format for better readability and organization (#OEvortex)

## Version 7.8 (April 2024)

### 2024-04-04

- 📝 **Documentation:** Revamped README with enhanced introduction, features, and installation instructions
  - Restructured content for better readability
  - Added comprehensive feature descriptions
  - Updated code examples for all major modules
  - Improved visual presentation with badges and formatting

### 2024-04-04

- 🔄 **Merge:** Integrated latest changes from main branch (#342d751)
- 📝 **Documentation:** Enhanced LEGAL_NOTICE.md with detailed attribution and licensing terms for improved clarity (#newcommitid)
- 🛠️ **Enhancement:** Added enhanced debugging and logging functionality with lit and litprint modules (#9b5a9cb)
- 💄 **Style:** Improved README banner presentation (#6bae2d6)

### 2024-04-03

- ✏️ **Rename:** Changed rawdog.py to autocoder.py (#529f514)
- 📝 **Documentation:** Made intro content shorter and more concise (#8bb7b81, #66e6e8c)
- 🔧 **Update:** Enhanced conversation.py prompting system (#6401a8f)
- ⚙️ **Feature:** Enhanced YEPCHAT provider with tool calling functionality and updated Conversation class to support tool management (#27c8370)
  - Added example usage for weather tool in new script

### 2024-04-02

- 🔨 **Refactor:** Updated imports to use 'litagent' module for LitAgent across multiple provider files (#51505ee)
- 🔼 **Version:** Bumped version to 7.8 in version.py (#f04d3c3)
- 🏷️ **Rename:** Changed GoogleS to GoogleSearch and enhanced search functionality (#023eb8b)
  - Improved error handling
  - Added support for text and news searches
  - Refined response parsing
  - Updated README with new usage examples

### 2024-04-01

- 🗑️ **Remove:** Deprecated autocoder_usage.py (#6d81d93)
- 🔄 **Update:** Enhanced available models in FreeAIChat and FreeAIPlayground providers (#6d81d93)
  - Added new models
  - Improved model name clarity for better user understanding
- 🔄 **Merge:** Synchronized with main repository branch (#2b90ea9)
- 🐛 **Fix:** Added "NOT WORKING" comment to oivscode.py and updated type hints (#39a97ea)
  - Included debugging print statement for response text
- ✨ **Feature:** Added thinking capabilities to autocoder (#ec676f9, #c9ea446)
- 📝 **Documentation:** Updated README to include SearchChatAI provider (#ca350e5)
  - Enhanced TTS documentation with voice selection and logging details
  - Added SearchChatAI to **init**.py for improved provider integration

### 2024-03-31

- 📝 **Documentation:** Updated README to include Aitopia provider (#0d6ff18)
  - Enhanced the list of AI services
  - Added Aitopia to **init**.py for improved provider integration
- 🔄 **Update:** Modified README to remove Devs Do Code's YouTube link and enhanced formatting (#b8c581e)
  - Added AskSteve provider to **init**.py for improved functionality

## Version 7.7 (March 2024)

### 2024-03-30

- 🔄 **Merge:** Integrated latest changes from main branch (#3162f35)
- 📝 **Documentation:** Refactored comments in `multichat.py` for consistency and clarity (#e3af93c)
  - Updated README files in `AISEARCH` and `TTI` to include new provider details and enhance formatting
  - Added `pixelmuse` to the TTI provider list for improved documentation
- 🛠️ **Enhancement:** Updated TypeGPT (#cffcb35)
- 📝 **Documentation:** Updated README and refactored type hints in AISEARCH provider files (#71b9193)
  - Added `ExaChat` to the README and `__init__.py`
  - Enhanced type clarity in `DeepFind.py`, `felo_search.py`, `genspark_search.py`, and `ISou.py` by using `Union` in method signatures, improving code readability and maintainability

### 2024-03-29

- 🔨 **Refactor:** Refactored image upload and access token retrieval in `copilot.py` (#6ab7c7c)
  - Enhanced error handling
  - Streamlined image upload process
  - Improved retrieval of access tokens and cookies from HAR files
  - Updated WebSocket message handling for better response processing
- 🔨 **Refactor:** Refactored image upload handling in `copilot.py` to improve error handling and streamline the process (#2e66e80)
  - Added checks for the presence of the `nodriver` package
  - Enhanced the retrieval of access tokens and cookies
  - Updated image upload API endpoint and improved response handling for better reliability
- 🔨 **Refactor:** Refactored type hints in `multichat.py` to use `Union` in method signatures, enhancing type clarity and improving code readability and maintainability (#a46422c)
- 🔨 **Refactor:** Refactored type hints in `typegpt.py` to enhance type clarity by incorporating `Any`, `Dict`, and `Generator`, improving code readability and maintainability (#67dd265)
- 🔨 **Refactor:** Refactored type hints in `Marcus.py` to improve type clarity by using `Union` in method signatures, enhancing code readability and maintainability (#bc5c64b)
- 🔨 **Refactor:** Refactored type hints across multiple provider files to improve type clarity by using `Union` in method signatures, enhancing code readability and maintainability (#9322f5c)
- 🔨 **Refactor:** Refactored type hints in `askmyai.py` to improve type clarity by using `Union` in method signatures, enhancing code readability and maintainability (#447ca30)
- 🔨 **Refactor:** Refactored type hints across multiple provider files to use `Union` for improved type clarity and consistency in method signatures, enhancing code readability and maintainability (#db89ef1)
- 🔨 **Refactor:** Refactored type hints in `bagoodex.py` to use `Union` for improved type clarity in method signatures, enhancing code readability and maintainability (#2f26f8d)
- 🔨 **Refactor:** Refactored type hints in `Llama3.py` to improve type clarity by using `Union` in method signatures, enhancing code readability and maintainability (#e3c6196)
- 🔨 **Refactor:** Refactored type hints across multiple provider files to use `Union` for improved type clarity and consistency in method signatures, enhancing code readability and maintainability (#df142e2)
- 🔨 **Refactor:** Refactored type hints in `Llama.py` to use `Union` for improved type clarity in method signatures, enhancing code readability and maintainability (#23597fe)
- 🔨 **Refactor:** Refactored type hints in `AIutel.py` to use `Union` for improved type clarity in the `sanitize_stream` function, enhancing code readability and maintainability (#e0b817d)
- 🔨 **Refactor:** Refactored type hints in `tempid.py` to use `List` and `Optional` for improved type clarity and consistency in method signatures, enhancing code readability and maintainability (#09c7bdd)
- 🔨 **Refactor:** Refactored type hints in `tempid.py` to use `Optional` for nullable fields, enhancing type clarity and consistency across the `MessageResponseModel` class (#c60d832)
- 🔨 **Refactor:** Enhanced type hints in `webscout/utils.py` by adding `Union` to improve type clarity and support for multiple data types (#615062d)
- 🔄 **Update:** Updated README.md to include `VercelAI` in the list of providers (#ac45518)
  - Modified `setup.py` to require Python 3.9 or higher
  - Refactored type hints in `webscout/utils.py` for improved clarity
  - Enhanced multiple provider classes by updating response handling and adding new models in `Venice.py`
  - Cleaned up imports and streamlined code in `QwenLM.py`, `uncovr.py`, and `WiseCat.py` for better maintainability

### 2025-03-28

- 📝 **Documentation:** Updated README.md files across multiple TTI providers to improve clarity and formatting (#cc0df4b)
  - Added new sections and examples
  - Ensured consistent spacing
  - Enhanced error handling descriptions
  - Notable changes include the addition of features and installation instructions for AiForce and Nexra, as well as optimizations in Piclumen and Talkai documentation
- 📝 **Documentation:** Enhanced `README.md` in the TTI provider to include the new `ImgSys` provider (#cd1037f)
  - Offers multi-provider image generation with error handling and async support

### 2025-03-28

- 🔨 **Refactor:** Refactored `Gemini.py` to remove logging functionality and streamline model initialization (#f97d30d)
  - Updated model aliases to include `2.5-exp-advanced`
  - Adjusted type hints for clarity
  - Removed unnecessary comments and logging code to enhance maintainability
- 🔨 **Refactor:** Refactored `Bard.py` to streamline model definitions and improve code clarity (#1bebc4f)
  - Removed unnecessary line breaks in the `UPLOAD` header
  - Added new model `G_2_5_EXP_ADVANCED`
  - Marked several models as deprecated with comments for future removal
  - Updated type hints in the `from_name` method for consistency

### 2024-03-25

- 🗑️ **Remove:** Deprecated `t.py` file and updated version to 7.7 in `version.py` (#7a8a4e8)
  - Refactored user agent generation in `agent.py` for improved browser handling and randomization
- 🛠️ **Enhancement:** Enhanced AutoCoder and LearnFast modules with improved error handling, execution result capture, and streamlined response processing (#ab2d335)

### 2024-03-22

- 🛠️ **Fix:** Fixed various issues (#834413b)
- 🔄 **Merge:** Integrated latest changes from main branch (#45e9adb)
- 📝 **Documentation:** Updated README and Provider modules to include new AI providers: LabyrinthAI, WebSim, LambdaChat, and ChatGPTClone (#bce699e)
  - Refactored AllenAI to streamline prompt handling
  - Removed unused logging features from multiple providers, enhancing overall code clarity and maintainability

### 2024-03-22

- ✨ **Feature:** Removed logging and added new providers (#0a6c4e9)

### 2024-03-21

- 🛠️ **Enhancement:** Enhanced GliderAI to support both standard and DeepSeek response formats (#a4244b7)
  - Improved content extraction logic for streaming text
- 📝 **Documentation:** Updated README and Provider module to include UncovrAI provider (#a225ef6)
- 🔄 **Merge:** Integrated latest changes from main branch (#8a86d9e)
- ✨ **Feature:** Added weather functionality to CLI, including a new command for retrieving weather data and a dedicated display format (#73f4006)
  - Updated README with relevant links and installation instructions
- 🔨 **Refactor:** Refactored GGUF model conversion to utilize ModelConverter class (#9156122)
  - Enhanced README examples
  - Improved type hints across the codebase
  - Updated OLLAMA provider to support tools and images in chat methods
  - Adjusted TypeGPT API endpoint for consistency

### 2024-03-21

- 🛠️ **Fix:** Fixed various issues (#c0a9488, #b1d432c)

### 2024-03-20

- 🔼 **Version:** Updated version to 7.6, removed Amigo and Bing providers from the project, and cleaned up related imports in the Provider module (#fedac8b)
  - Adjusted README to reflect current model availability
- 📝 **Documentation:** Updated license to reflect new attribution and licensing terms (#9b1d861)
  - Removed logging options from GoogleS class
  - Streamlined provider testing in multiple classes
  - Removed DiscordRocks provider
  - Enhanced model availability checks and error handling across various providers

### 2024-03-19

- 🗑️ **Remove:** Deprecated Autollama utility and related documentation from README and imports (#8a0b8de)
- 🔨 **Refactor:** Refactored GGUF model conversion process to streamline temporary directory management and encapsulate conversion logic in a helper method (#5fbefeb)
  - Improved code organization and maintained functionality for both local and upload scenarios
- 🔨 **Refactor:** Updated GGUF model converter to include type hints for imports and improve train data path assignment logic (#1c6161b)
- 🛠️ **Enhancement:** Enhanced GGUF model conversion with advanced features including imatrix quantization, model splitting, and improved hardware detection (#b12a811)
  - Updated CLI options and README generation for better user guidance

### 2024-03-17

- ✨ **Feature:** Added FastFlux image generator provider and updated README (#f9a122b)
- 🗑️ **Remove:** Deprecated AI art generation function and related imports from test.py (#c2cfe81)
- ✨ **Feature:** Added MagicStudio provider for AI image generation and updated README (#d259aee)
- 🛠️ **Fix:** Fixed various issues (#9f6c1e0, #09bbb56, #1b6ce8b)

### 2024-03-16

- 🔨 **Refactor:** Refactored imports across multiple files to streamline code and remove unused dependencies (#0024425)
- 📝 **Documentation:** Updated README with AI Search Providers and removed proxy rotation example from LitAgent documentation (#64701f2)
- 🛠️ **Enhancement:** Enhanced LitAgent with new device types, browser fingerprinting support, and updated documentation (#4744b36)
- ✨ **Feature:** Added TTS voice management functionality and updated README (#2cb678a)
- 🔨 **Refactor:** Refactored TTS provider imports, removed Voicepods provider, and updated README for new SpeechMa provider (#6ee2331)
- 📝 **Documentation:** Added weather toolkit documentation, implemented model management, and created GitHub workflows for labeling and releases (#c8721cb)

### 2024-03-14

- 🗑️ **Remove:** Deprecated pygetwindow dependency from autocoder_utiles.py (#c8f16b3)
- 🔼 **Version:** Bumped version to 7.5 (#c0226af)
- ✨ **Feature:** Added Flowith provider implementation and updated README (#82c1d38)
- 🗑️ **Remove:** Deprecated logging functionality from Cloudflare and DeepSeek providers (#671c75f)
  - Updated README to reflect changes in available models
- ✨ **Feature:** Added system prompt parameter to HuggingFaceChat initialization (#34d55c2)
- 🔄 **Merge:** Integrated latest changes from main branch (#7a0cb5a)
- 🔨 **Refactor:** Refactored DeepInfra and HuggingFaceChat providers (#9b45b6e)
  - Updated available models
  - Enhanced initialization with assistantId

### 2024-03-14

- 🔄 **Merge:** Integrated latest changes from main branch (#3c965e4, #160e127, #1f4a42a, #604d8e1)
- 🛠️ **Enhancement:** Added Dependabot configuration and workflows for automated dependency management and review (#ac8c50c)
- ✨ **Feature:** Added C4ai provider and updated README (#2da854f)
- 🔨 **Refactor:** Updated AkashGPT provider to comment out unused models and add system prompt to request payload (#5c4ad7d)
- ✨ **Feature:** Added AIArta provider with synchronous and asynchronous interfaces, and introduced AuthenticationError exception (#4ddc4a0)
- 🔨 **Refactor:** Refactored Phind and Marcus providers to standardize available models and remove logging functionality (#5338e70)
- ✨ **Feature:** Added nodriver dependency and included Copilot provider in the module exports (#b11d4a6)
- 🗑️ **Remove:** Deprecated format_prompt method from GithubChat provider (#0840b5c)
- 📝 **Documentation:** Added site removal request templates and legal notice (#1e7043d)
- ✨ **Feature:** Added GithubChat to provider list and updated README (#ae43b98)
- ✨ **Feature:** Added HuggingFaceChat to provider list and updated README (#6aed37b)

### 2024-03-09

- 🔄 **Merge:** Integrated latest changes from main branch (#e492880, #2526692, #3c9bc83)
- 🛠️ **Fix:** Fixed various issues (#e5c666c, #4784a79)
- 🔨 **Refactor:** Removed webscout.Local (#e5c666c)
- 🔼 **Version:** Bumped version to 7.4 (#4784a79)
- ✨ **Feature:** Added plus_model parameter to initialize ChatGLM API client (#88670e9)
- 🔨 **Refactor:** Removed logging functionality and updated model names in QwenLM provider (#3b05a18)
- 🛠️ **Fix:** Updated model name from "qwq-32b-preview" to "qwq-32b" in QwenLM provider (#638dcc0)

### 2024-03-08

- 🔄 **Merge:** Integrated latest changes from main branch (#edc6cea, #7ad8708, #6b46674, #ee79c12)
- 🛠️ **Enhancement:** Enhanced security and fixed text encoding for Cyrillic and other encodings (#7ad8708, #6b46674, #ee79c12)
  - Updated the list of models
  - Fixed function for_non_stream

### 2024-03-06

- ✨ **Feature:** Added PiclumenImager provider with synchronous and asynchronous support (#92f4e43)
  - Enhanced README with usage examples

### 2024-03-05

- ✨ **Feature:** Added Venice AI provider with API integration and model support (#0396126)
- ✨ **Feature:** Implemented TwoAI provider with API integration and model support (#2a892b7)
- ✨ **Feature:** Added HeckAI provider with API integration and model support (#077ae14)
- ✨ **Feature:** Added AllenAI to the list of available models in the README (#b0267c5)
- ✨ **Feature:** Updated model selection and validated against available models in KOALA provider (#701563f)
- ✨ **Feature:** Updated available models and removed logging functionality in Jadve provider (#be93810)
- ✨ **Feature:** Updated User-Agent to use LitAgent for dynamic generation in ChatGLM provider (#48ac416)
- 🔨 **Refactor:** Removed logging functionality from WiseCat and YEPCHAT classes (#c503120)
- 🔨 **Refactor:** Removed logging capabilities and simplified initialization in GliderAI and DeepInfra providers (#7f4b98b)
- ✨ **Feature:** Added PerplexityLabs to provider list and updated README with new model (#bf82326)
- ✨ **Feature:** Added customizable system prompt for conversation initialization in ElectronHub provider (#a1eee9e)
- ✨ **Feature:** Added ElectronHub provider supporting 371 AI models (#1a9f330)
- ✨ **Feature:** Added GitHub data extraction module with user and repository functionalities in GitAPI (#4559c60)
- ✨ **Feature:** Added AkashGPT to provider list and updated README with new model (#2d48123)
- ✨ **Feature:** Updated AVAILABLE_MODELS list by removing and adding new models in FreeAIChat provider (#aa9834b)
- ✨ **Feature:** Added Genspark providers with examples and documentation updates in AISearch (#56804de)
- ✨ **Feature:** Added voice support with logging and enhanced voice configuration in PiAI provider (#56804de)
- ✨ **Feature:** Added AVAILABLE_MODELS list and updated default model with validation in DeepInfra provider (#dc340cb)

### 2024-03-02

- 🔼 **Version:** Bumped version to 7.3 (#107a59e)
- ✨ **Feature:** Enhanced AVAILABLE_MODELS with detailed descriptions for each model in TextPollinationsAI provider (#a47ef31)
- ✨ **Feature:** Added synchronous and asynchronous methods for retrieving weather information from DuckDuckGo (#b17c429)
- ✨ **Feature:** Added suggestions method to YepSearch class for autocomplete functionality (#3b1970a)
- ✨ **Feature:** Added YepSearch class for text and image search functionality (#ab1285f)
- 🛠️ **Fix:** Added missing comma in BUILD_ARTIFACTS and updated AVAILABLE_MODELS in YEPCHAT provider (#40bd2a2)

### 2024-03-01

- ✨ **Feature:** Implemented FreeAIChat provider with multi-model support (#52dd9a2)
- ✨ **Feature:** Added FreeAIImager provider with DALL-E 3 & Flux models (#ca6a4c3)
  - Implemented new TTI provider with support for 7 premium models
  - Added both sync (FreeAIImager) and async (AsyncFreeAIImager) classes
  - Included comprehensive documentation and usage examples
  - Supported models: DALL-E 3, Flux Pro Ultra, Flux Pro, Flux Realism, etc.

## Version 7.2 (February 2024)

### 2024-02-25

- 🔄 **Merge:** Integrated latest changes from main branch (#4c820e9)
- 🛠️ **Fix:** Solved problem with pydantic import error in Bard provider and made replace_links_with_numbers function available (#b4a8868)

### 2024-02-24

- 🔄 **Merge:** Integrated latest changes from main branch (#09cb4ef)
- 🛠️ **Enhancement:** Enhanced logging system with new log levels, formats, and console handler improvements (#32fad16)

### 2024-02-23

- 🔄 **Merge:** Integrated latest changes from main branch (#8ee4372)
- 🛠️ **Fix:** Added resource cleanup method (#18b3a1a)
- 🔨 **Refactor:** Updated code (#ad7e21a)
- ✨ **Feature:** Implemented core logging functionality with handlers and utilities (#e175955)
- ✨ **Feature:** Added WiseCat provider (#ecb240d)

### 2024-02-22

- ✨ **Feature:** Enhanced GEMINI provider with model support and logging capabilities (#60a80f2)
- 🔄 **Update:** Updated Cerebras available models (#1f72427)
- 🔨 **Refactor:** Cleaned up docstrings and updated deprecated model mappings (#0034659)

### 2024-02-18

- ✨ **Feature:** Added new models to the GROQ provider (#e7e39c3)

### 2024-02-14

- 🔄 **Merge:** Integrated latest changes from main branch (#2b56a52)
- 🛠️ **Enhancement:** Enhanced code safety and fixed for_non_stream method in QwenLM provider (#bbbbbd3, #7291098)
  - Added ability to use different types of chats (t2t, search, t2i, t2v)

### 2024-02-13

- ✨ **Feature:** Added QwenLM provider to the list of available providers in the API (#cd03cdc)
- 🛠️ **Fix:** Updated deprecated model mappings for llama variants (#7a8d77e)

### 2024-02-10

- 🔄 **Merge:** Integrated latest changes from main branch (#4e8ab51, #71ec978, #55f6979)
- ✨ **Feature:** Added support for Claude variant in Free2GPT API client (#55f6979)
- ✨ **Feature:** Added ChatGPTGratis provider with logging and streaming capabilities (#a3ec214)
- 🛠️ **Fix:** Updated setup.py (#e5b5f0b, #6282524)

### 2024-02-10

- 🔨 **Refactor:** Updated README formatting, removed yaspin dependency, and bumped version to 7.1 (#5123775)
- ✨ **Feature:** Added models & logger (#63f6b0c)
- ✨ **Feature:** Added logging and litagent in deepinfra (#6458c31)
- ✨ **Feature:** Added logging capabilities to DGAFAI class (#726a49c)
- ✨ **Feature:** Added comprehensive logging to GliderAI class (#a1eda85)
- ✨ **Feature:** Added logging functionality to GaurishCerebras API client and modified response handling in chat and ask methods (#c28572b)
- ✨ **Feature:** Added logging functionality to JadveOpenAI class and improved code readability with comments and docstrings (#75d583b)
- ✨ **Feature:** Added LitLogger to LlamaTutor provider (#4699c82)
- ✨ **Feature:** Enhanced BlackboxAI session generation with optional email input and diverse name/domain lists for greater realism.
- ✨ **Feature:** Added Microsoft Copilot provider integration to OPENAI module.
  - Included Copilot in provider list.
  - Updated `webscout\Provider\OPENAI\__init__.py` for Copilot import.
  - Added `webscout\Provider\OPENAI\copilot.py` to support Microsoft Copilot as an OpenAI-compatible provider.
- ✨ **Feature:** Enhanced AUTO provider to automatically exclude providers requiring authentication tokens or cookies. (#OEvortex)
- 🔧 **Feature:** Added option to print successful provider name in AUTO provider for better debugging. (#OEvortex)
- ✨ **Feature:** Implemented OpenAI-compatible interface for TypefullyAI provider with streaming support and standardized prompt formatting. (#OEvortex)
- 🔄 **Update:** Refreshed model list for TextPollinationsAI provider with latest available models. (#OEvortex)
- 🔄 **Update:** Updates model mapping in SciraChat providers
- 🐛 **Fix:** Enhanced shell command handling with `!` prefix in autocoder: (#OEvortex)
  - Modified `_extract_code_blocks` to properly detect shell commands in code blocks
  - Added support for shell commands in triple backticks without language tag
  - Implemented Jupyter-style UI for shell command execution and output display
  - Fixed issue with `main` method not properly handling shell commands
  - Added support for multiple shell commands in a single code block
  - Enhanced error handling and display for shell commands
- 🔧 **Feature:** Added limit parameter to trending video methods and updated model mapping: (#OEvortex)
  - Introduced optional limit parameter to all trending video retrieval methods
  - Allows trending video results to be capped directly within method calls
  - Updated AI model mapping to include support for an additional model
  - Improved provider flexibility with enhanced model support

## Version 8.2.6 (May 2025)

### 2025-05-05

- ✨ **Feature:** Added new model support for `GizAI` provider with enhanced API error handling. (#OEvortex)
- 🔨 **Refactor:** Optimized response streaming in `ChatSandbox` and `TypliAI` providers for better performance. (#OEvortex)
- 📝 **Documentation:** Updated README with new examples for GGUF converter usage. (#OEvortex)

### 2025-05-04

- ✨ **Feature:** Implemented batch processing capability in `MultiChatAI` provider. (#OEvortex)
- 🔧 **Change:** Updated default timeout values across all providers for better reliability. (#OEvortex)
- 🐛 **Fix:** Resolved memory leak issue in `TwoAI` streaming implementation. (#OEvortex)

### 2025-05-03

- ✨ **Feature:** Added experimental support for `SonusAI` voice synthesis models. (#OEvortex)
- 🔨 **Refactor:** Cleaned up import statements in `ElectronHub` for better code organization. (#OEvortex)
- 📝 **Documentation:** Added troubleshooting section for GGUF converter in README. (#OEvortex)

## Version 8.2.5 (May 2025)

### 2025-05-02

- 🔧 **Change:** Removed `inferno` folder and made it a standalone package: `inferno-llm` (available via `pip install inferno-llm`). (#OEvortex)
- 🔧 **Change:** Removed `webscout/Local` module as it's now part of the standalone Inferno package. (#OEvortex)
- 📝 **Documentation:** Updated README to reflect Inferno is now a standalone package with links to GitHub and PyPI repositories. (#OEvortex)
- ✨ **Feature:** Implemented `GizAI` provider for API interaction and enhanced response handling. (#OEvortex)
- 📝 **Documentation:** Added detailed documentation for GGUF converter with comprehensive usage examples and features. (#OEvortex)
- ✨ **Feature:** Implemented Google and Yep search commands in CLI with configurable options for region, safesearch, and result filtering. (#OEvortex)
- 🔨 **Refactor:** Cleaned up message validation logic in conversation module for improved reliability. (#OEvortex)

### 2025-05-01

- ✨ **Feature:** Added `ChatSandbox` and `TypliAI` providers with enhanced API interaction capabilities. (#OEvortex)
- 📝 **Documentation:** Updated README to add `MultiChatAI`, `AI4Chat`, and `MCPCore` to available providers list. (#OEvortex)
- ✨ **Feature:** Updated `TwoAI` API endpoint and enhanced streaming response handling for better performance. (#OEvortex)
- 🔨 **Refactor:** Cleaned up import statements in `ElectronHub` and `Glider` files for improved code readability. (#OEvortex)
- 🔨 **Refactor:** Integrated `sanitize_stream` for improved response handling across multiple providers: (#OEvortex)
  - Added to `MultiChatAI` for processing raw responses
  - Updated `SciraAI` for both streaming and non-streaming responses with error handling
  - Implemented in `SCNet` for JSON extraction from streaming data
  - Enhanced `SearchChatAI` for efficient data processing
  - Integrated in `SonusAI` for better content extraction from responses
  - Refactored `Toolbaz` to use `sanitize_stream` for tag removal in streaming text
  - Updated `TurboSeek` for JSON object extraction
  - Implemented in `TypefullyAI` for improved content extraction from streaming responses
  - Enhanced `TypeGPT` for both streaming and non-streaming responses
  - Integrated in `UncovrAI` for better handling of streaming and non-streaming data

## Version 8.2.4 (May 2025)

### 2025-05-01

- ✨ **Feature:** Enhanced `AIutel.py` chunk processing with byte stream decoding and integrated `sanitize_stream` across multiple providers (`yep.py`, `x0gpt.py`, `WiseCat.py`, `WritingMate.py`, `Writecream.py`, `HeckAI.py`) for improved data handling and cleaner code. (#OEvortex)

### 2025-04-30

- ✨ **Feature:** Implemented `MCPCore` API client (`Provider/OPENAI/mcpcore.py`) with model support and cookie handling. (#OEvortex)

### 2025-04-29

- ✨ **Feature:** Updated available models list for `HeckAI` provider. (#OEvortex)
- ✨ **Feature:** Updated available models list for `DeepInfra` and `ElectronHub` providers, adding dynamic model fetching. (#OEvortex)

### 2025-04-27

- ✨ **Feature:** Implemented `Groq` client (`Provider/OPENAI/groq.py`) for chat completions, switching API usage and updating model handling. (#OEvortex)
- ✨ **Feature:** Implemented model fetching from Groq API, updated available models, and switched to `curl_cffi` for HTTP requests in `Groq` provider (`Provider/Groq.py`). (#OEvortex)
- 🔨 **Refactor:** Refactored `ChatGPTClone` to use `curl_cffi`, removed `ChatGPTES`, added `AI4Chat`, enhanced error handling, and updated headers/session initialization across providers. (#OEvortex)

### 2025-04-25

- ✨ **Feature:** Added GGUF RAM estimation utilities and `MultiChatAI` provider implementation with support for multiple endpoints and streaming. (#OEvortex)

### 2025-04-23

- 🔨 **Refactor:** Replaced `primp` library with `curl_cffi` for HTTP requests across the `webscout` package. (#OEvortex)

## Version 8.2.3 (23 April 2025)

### 2025-04-23

- ✨ **Feature:** Implemented base TTS provider with audio saving and streaming functionality (#OEvortex)
  - Added foundational TTS provider class
  - Enabled audio file saving and streaming support

### 2025-04-22

- ✨ **Feature:** Updated available models in Toolbaz provider (#OEvortex)

### 2025-04-21

- 🗑️ **Remove:** Removed unfinished E2B API and Emailnator implementations (now completed) (#OEvortex)

## Version 8.2.2 (20 April 2024)

### 2024-04-20

- ✨ **Feature:** Added new models to E2B provider (#OEvortex)

  - Added support for o4-mini, gpt-4o-mini, gpt-4-turbo models
  - Added support for Qwen2.5-Coder-32B-Instruct model
  - Added support for DeepSeek R1 model

- 🔧 **Fix:** Updated Dependabot reviewer username to OEvortex (#OEvortex)

- 🔧 **Fix:** Fixed issues in the inferno CLI module (#OEvortex)

### 2024-04-19

- ✨ **Feature:** Implemented Emailnator provider for TempMail and updated provider list (#OEvortex)
  - Added new temporary email provider
  - Updated provider listings to include the new service

## Version 8.2.1 (19 April 2024)

### 2024-04-19

- ✨ **Feature:** Added E2B provider to OPENAI directory (#OEvortex)
  - Implemented OpenAI-compatible interface for E2B API
  - Added support for various models including claude-3.5-sonnet
  - ~~Enabled both streaming and non-streaming completions~~
  - Included comprehensive error handling and response formatting

## Version 8.2 (18 April 2024)

### 2024-04-18

- ✨ **Feature:** Implemented webscout.Local module with command-line interface (#OEvortex)

  - Added cli.py for managing models, including commands to serve, pull, list, remove, and run models
  - Integrated model management and loading functionalities
  - Enhanced user interaction with rich console outputs and prompts

- ✨ **Feature:** Added configuration management for webscout.Local (#OEvortex)

  - Introduced config.py to handle application configuration
  - Implemented loading, saving, and accessing configuration values
  - Default configurations for models directory, API host, and port

- ✨ **Feature:** Created LLM interface for local model integration (#OEvortex)

  - Developed llm.py to interface with llama-cpp-python for model loading and completion generation
  - Added methods for creating completions and chat responses

- ✨ **Feature:** Implemented model management functionalities (#OEvortex)

  - Created model_manager.py for downloading, listing, and removing models
  - Integrated Hugging Face Hub for model downloads and file management

- ✨ **Feature:** Implemented OpenAI-compatible API server (#OEvortex)

  - Added server.py to create an OpenAI-compatible API using FastAPI
  - Implemented endpoints for model listing and chat/completion requests

- ✨ **Feature:** Added utility functions for webscout.Local (#OEvortex)

  - Introduced utils.py for various utility functions including duration parsing and image encoding/decoding

- ✨ **Feature:** Added Perplexity search provider and updated README with examples (#OEvortex)

- ✨ **Feature:** Added XAI model configuration and updated available models in ExaChat (#OEvortex)

- ✨ **Feature:** Added WritingMate provider and updated cleanup script to remove .pytest_cache (#OEvortex)

- ✨ **Feature:** Updated available models in SciraAI and SciraChat (#OEvortex)

- ✨ **Feature:** Integrated TextPollinations API and updated related models (#OEvortex)

### 2024-04-17

- ✨ **Feature:** Switched from OPKFC to ChatGPT and updated model to auto (#OEvortex)

- 🧹 **Cleanup:** Removed all compiled Python files (.pyc) from the **pycache** directories (#OEvortex)

  - Ensured a clean build environment and prevented potential issues with stale bytecode

- ✨ **Feature:** Added OPKFC as new provider (#OEvortex)

- ✨ **Feature:** Added scira-o4-mini model to available models in SciraChat and SciraAI (#OEvortex)

- ✨ **Feature:** Implemented UncovrAI API integration and updated related files (#OEvortex)

### 2024-04-16

- ✨ **Feature:** Updated endpoints and added new models for ExaChat, GithubChat, Glider, and YouChat (#OEvortex)

### 2024-04-15

- ✨ **Feature:** Added Toolbaz and SCNet API implementations (#OEvortex)

  - Updated **init**.py for new providers

- ✨ **Feature:** Implemented Writecream API integration and updated client initialization (#OEvortex)

- ✨ **Feature:** Added StandardInputAI and E2B API implementations (#OEvortex)
  - Implemented StandardInputAI class for interacting with the Standard Input chat API
  - Added E2B class for encapsulating the E2B API, supporting various models
  - Included methods for building request bodies, merging user messages, and generating system prompts
  - Enhanced error handling and response parsing for API requests

### 2024-04-14

- ✨ **Feature:** Enhanced setup.py with additional classifiers and keywords (#OEvortex)

## Version 8.1 (14 April 2024)

### 2024-04-14

- ✨ **Feature:** Added OpenAI-compatible interfaces for multiple providers, enabling standardized API access (#OEvortex)

  - Implemented OpenAI-compatible interfaces for DeepInfra, Glider, ChatGPTClone, X0GPT, WiseCat, Venice, ExaAI, TypeGPT, SciraChat, LLMChatCo, FreeAIChat, and YEPCHAT
  - Added comprehensive documentation with usage examples for all OpenAI-compatible providers
  - Created standardized response formats matching OpenAI's structure for better compatibility

- 🔧 **Fix:** Resolved minor bugs in native compatibility implementations (#OEvortex)

  - Enhanced error handling and response processing across multiple providers
  - Improved model validation and selection logic
  - Standardized timeout handling for better reliability

- 📝 **Documentation:** Added detailed README for OpenAI-compatible providers with examples and model listings (#OEvortex)
  - Created comprehensive provider-specific documentation
  - Added code examples for both streaming and non-streaming usage
  - Updated main README with information about dual compatibility options

## Version 8.0 (13 April 2024)

### 2024-04-13

- 🔼 **Version:** Updated version to 8.0 (#OEvortex)
- ✨ **Feature:** Added SciraAI search provider with streaming support, multiple models, and DeepSearch capabilities (#OEvortex)
- ✨ **Feature:** Introduced 'gemini-2.5-pro' model to GitHub Chat for advanced interactions (#OEvortex)
- ✨ **Feature:** Enhanced DeepInfra with configurable system prompts and updated model availability (#OEvortex)
- ✨ **Feature:** Improved model configurations for Hika, ExaAI, and Netwrck providers (#OEvortex)
- ✨ **Feature:** Added support for new providers: OpenGPT, WebpilotAI, Hika, ExaAI, LLMChatCo, and TypefullyAI (#OEvortex)
- 🗑️ **Remove:** Removed non-functional models from DeepInfra for a cleaner experience (#OEvortex)
- ✨ **Feature:** Enhanced video metadata extraction with additional properties for better insights in YTToolkit (#OEvortex)
- ✨ **Feature:** Added retry logic and Turnstile token handling to improve AI chat functionality (#OEvortex)
- 🔨 **Refactor:** Refactored URL handling and error management for more reliable operations (#OEvortex)
- 🔨 **Refactor:** Streamlined provider configurations and removed deprecated entries (#OEvortex)

## Version 7.9 (April 2024)

### 2024-04-09

- 🔼 **Version:** Updated version to 7.9 (#OEvortex)
- 🗑️ **Remove:** Removed Editee provider and updated imports (#OEvortex)
- ✨ **Feature:** Updated ElectronHub AVAILABLE_MODELS with new AI model entries (#OEvortex)
- ✨ **Feature:** Added Llama 4 Scout and Llama 4 Maverick to FreeAIChat AVAILABLE_MODELS (#OEvortex)
- ✨ **Feature:** Updated Gemini model aliases and removed deprecated entries (#OEvortex)

### 2025-04-08

- 💄 **Style:** Standardized formatting and indentation in system context prompts for optimizers (#OEvortex)
- ✨ **Feature:** Added informative error raising if litprinter is not installed (#OEvortex)

### 2025-04-06

- ✨ **Feature:** Added "qwen25-coder-32b-instruct" to LambdaChat AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Added cerebras models and updated gemini model list in ExaChat (#OEvortex)
- ✨ **Feature:** Updated UncovrAI AVAILABLE_MODELS and enhanced error handling in response parsing (#OEvortex)
- ✨ **Feature:** Updated TextPollinationsAI AVAILABLE_MODELS list with new models and improved descriptions (#OEvortex)
- ✨ **Feature:** Restored google gemma models to DeepInfra AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Updated GROQ AVAILABLE_MODELS list with new models and removed commented entries (#OEvortex)
- ✨ **Feature:** Added new models to DeepInfra AVAILABLE_MODELS list (#OEvortex)

### 2025-04-05

- 🗑️ **Remove:** Removed DARKAI provider and updated imports (#OEvortex)
- ✨ **Feature:** Added new models to FreeAIChat AVAILABLE_MODELS list (#OEvortex)
- ✨ **Feature:** Implemented TempMail package for temporary email generation (#OEvortex)
- 📝 **Documentation:** Clarified fallback behavior for litprinter import (#OEvortex)
- 🔨 **Refactor:** Replaced bundled litprinter implementation with external package import (#OEvortex)
- 🐛 **Fix:** Updated import statements and removed redundant warnings for better clarity in traceback (#OEvortex)
- 📝 **Documentation:** Revamped README with enhanced introduction, features, and installation instructions (#OEvortex)
- 📝 **Documentation:** Enhanced legal notice with clearer disclaimers and updated licensing terms (#OEvortex)
- 📝 **Documentation:** Updated changelog.md with a professional and modern format for better readability and organization (#OEvortex)

## Version 7.8 (April 2024)

### 2024-04-04

- 📝 **Documentation:** Revamped README with enhanced introduction, features, and installation instructions
  - Restructured content for better readability
  - Added comprehensive feature descriptions
  - Updated code examples for all major modules
  - Improved visual presentation with badges and formatting

### 2024

- ✨ **Feature:** Added UI (#401ff60)
- 🔄 **Update:** Made some changes (#c20a0f9)
- 🛠️ **Fix:** Fixed small bug (#744f7ed)
- 🔄 **Update:** Made some improvements in Webscout (#1e130c9)

### 2024-07-12

- 🔄 **Update:** Made changes (#b2bb531)

### 2024-07-08

- ✨ **Feature:** Added new provider and fixed llama (#25f19d3)

### 2024-07-06

- ✨ **Feature:** Added Ollama provider (#256f484)

### 2024-07-04

- ✨ **Feature:** Added all non-api providers to AIauto (#84c6b0e, #01113c5)

### 2024-07-03

- 🔼 **Version:** Bumped version to 4.0 (#53ad7b9)

### 2024-07-02

- ✨ **Feature:** Updated CLI and added ytdownloader, weather (#fa901cf, #979671f)

### 2024-07-01

- ✨ **Feature:** Added weather fetch (#36f43a1)

### 2024-06-28

- 🛠️ **Fix:** Fixed various issues (#a253e29)
- ✨ **Feature:** Added more providers and optimized rawdog (#650626e)

### 2024-06-27

- 🔄 **Update:** Updated test.py (#dfe5a99)

### 2024-06-26

- ✨ **Feature:** Added new files (#169fd79, #6e066e3, #67924d3, #f41563e, #cd31247, #8e5fa54, #732d07a, #cb7e3cf, #b674170, #af8b162, #3cc6c49, #cc6c55e, #92449a7, #8b1f698, #837fb99)

### 2024-06-22

- 🔼 **Version:** Bumped version to 3.6 (#363d0f0)
- ✨ **Feature:** Added error fixer for internal rawdog (#fcb29c0, #38b45aa)
- ✨ **Feature:** Added phind and opengptv2 providers (#cff1c1b)

### 2024-06-16

- ✨ **Feature:** Added VLM, deepinfra, WEBSX providers and fixed DWEBS (#8a3418b, #1856287)

### 2024-06-14

- 🛠️ **Fix:** Fixed various issues (#c5fa438)

### 2024-06-06

- 🔄 **Update:** Updated history (#e3120ac)

### 2024-06-04

- ✨ **Feature:** Added new project (#06a027a)

### 2024-06-03

- ✨ **Feature:** Added rawdog to local (#c743c02)

### 2024-05-30

- 🗑️ **Remove:** Deleted build/lib directory (#0543861)
- ✨ **Feature:** Added function calling (#68ae561)

### 2024-05-26

- 🔼 **Version:** Bumped version to 2.9 (#cd78641)

### 2024-05-21

- 🛠️ **Fix:** Fixed various issues (#7b5b7e3, #26002be)

### 2024-05-19

- 🛠️ **Fix:** Solved small issues (#cf82395, #233986c)

### 2024-05-16

- 🔄 **Update:** Updated **init**.py (#112088e)

### 2024-05-15

- ✨ **Feature:** Added new project (#6e089bc)

### 2024-05-14

- 🛠️ **Fix:** Fixed various issues (#8ae0edb, #dfbd426)
- 🔼 **Version:** Bumped version to 2.4 (#416cc94)
- 🔄 **Merge:** Integrated latest changes from main branch (#6ebbaba)
-
- 🛠️ **Fix:** Solved issue with youchat (#db4a122)

### 2024-05-06

- 🔄 **Update:** Updated setup.py (#98fcceb, #a8a4e83, #f4e34cd)

### 2024-05-04

- ✨ **Feature:** Added temp mail and number (#3d41434)
- 📝 **Documentation:** Updated README.md (#def99db)

### 2024-05-03

- 🛠️ **Fix:** Solved small issues (#2a392a4)
- 🔄 **Update:** Updated setup.py (#61fc894)
- 🔼 **Version:** Bumped version to 1.3.9 (#f0f701c)

### 2024-04-27

- 🔼 **Version:** Bumped version to 1.3.8 (#43365b6)

### 2024-04-26

- ✨ **Feature:** Added new provider (#7f04d08)
- ✨ **Feature:** Added new files (#f83bbc4, #1c85e56, #5ac8675)

### 2024-04-22

- 🗑️ **Remove:** Deleted .circleci directory (#b20e03b)
- 🔄 **Update:** Updated setup.py (#04ed965, #b71f1ab, #002e931, #16dc95f)
- 🔄 **Merge:** Integrated latest changes from main branch (#9f22f9a)
- ✨ **Feature:** Added CircleCI commit (#b53ff01)

### 2024-04-20

- 🛠️ **Fix:** Solved typing error in setup.py (#b688112)
- 🛠️ **Fix:** Solved typing error in webai (#0a9591a)
- 🔄 **Merge:** Integrated latest changes from main branch (#eec1b00)
- ✨ **Feature:** Added webai and solved some issues (#a8a3c01, #20f5c7a)

### 2024-04-19

- ✨ **Feature:** Added new files (#d37229c)
- 🛠️ **Fix:** Solved LLM issue and added v1.3.3 (#5bf2c02, #9dbd955, #953e3c6)
- 🔄 **Update:** Updated **init**.py (#27f7fb2)
- 🔄 **Update:** Updated setup.py (#186e6fe)
- ✨ **Feature:** Added sean and testing webai (#b663a4b)
- ✨ **Feature:** Added new LLM models and solved issues related to appdirs (#86bdc4b)

### 2024-04-16

- ✨ **Feature:** Added TTS in webscout (#8b481ab, #1131463)

### 2024-04-12

- 🛠️ **Fix:** Fixed small issues (#fad2ba4)

### 2024-04-11

- 🔄 **Update:** Updated **init**.py (#aeb79c2)
- 📝 **Documentation:** Updated AsyncWEBS example code (#cfb4b96)

### 2024-04-09

- 🔼 **Version:** Bumped version to 1.2.8 (#0ce7881)

### 2024-04-07

- ✨ **Feature:** Added transcriber (#59f0b2f)

### 2024-04-03

- 🗑️ **Remove:** Deprecated offline AI and added KOBOLDAI (#83de7b9)

### 2024-04-02

- ✨ **Feature:** Added offline AI via gpt4all (#769bc88)

### 2024-03-31

- 📝 **Documentation:** Renamed CONTRIBUTING.md to CONTRIBUTE.md (#7c52f6b)
- 📝 **Documentation:** Created CONTRIBUTING.md (#0b0e59a)
- 🗑️ **Remove:** Deleted **pycache** directory (#d7c1eff)
- 🛠️ **Fix:** Added error handling in deepwebs and solved some issues (#61c6f73)
- 🗑️ **Remove:** Deleted DeepWEBS/files directory (#aa15feb)

### 2024-03-30

- ✨ **Feature:** Added DeepWEBS (#2e9c94a)
- 🔼 **Version:** Bumped version to 1.2.1 (#fd0a6c3)
- 🔼 **Version:** Bumped version to 1.2.0 (#1f8f4d9)
- 🔼 **Version:** Bumped version to 1.1.9 (#cb71ad4)

### 2024-03-29

- 🗑️ **Remove:** Deleted webscout-api/README.md (#bdb0da5)
- 🔄 **Update:** Updated flasksapi.py (#8c01ec5)
- 🗑️ **Remove:** Deleted webscout-api/API.py (#36b083d)

### 2024-03-24

- 🛠️ **Fix:** Solved issue (#ff58f52)
- 🛠️ **Fix:** Solved issue with CLI and added some cool things (#686cd0e, #14f7ca9)
- ✨ **Feature:** Added webscout new version (#cf400cf)
- ✨ **Feature:** Added openGPT (#79ba15e)
- ✨ **Feature:** Added perplixity (#56c929f)
- ✨ **Feature:** Added BlackBox and solved issue with phind (#1fbfbae)

### 2024-03-15

- ✨ **Feature:** Added new files (#a699f61)

### 2024-03-10

- 🛠️ **Fix:** Solved issue (#885b5fa)

### 2024-03-06

- 📝 **Documentation:** Updated README.md (#cdaf96d, #7d5b05c, #f71ef0d)
- 🗑️ **Remove:** Deleted API.md (#9f5d2ba)
- 📝 **Documentation:** Created API.md (#b5e2f7b, #b638fbe)
- ✨ **Feature:** Added webscout API (#65a56c4)
- 🔄 **Update:** Updated setup.py (#944c77d)
- 🗑️ **Remove:** Deleted HelpingAI.py (#bdd185e)
- ✨ **Feature:** Added new files (#046a45a, #53699a9)
- 🔼 **Version:** Bumped version to 1.0.4 (#a3664e5)
- 🛠️ **Fix:** Solved gemmni and added new features (#a49d072)
- ✨ **Feature:** Added HelpingAI and solved some issues (#b85c733)

### 2024-02-28

- 🗑️ **Remove:** Deleted test.py (#6d6af38)
- 🛠️ **Fix:** Solved gemmni (#7d386b5)
- ✨ **Feature:** Added LLM (#920c488)
- ✨ **Feature:** Added Prodia as image generator in webscout.AI (#22cafc7)
- 🔄 **Update:** Updated setup.py (#46f0f3a)

### 2024-02-27

- 📝 **Documentation:** Updated README.md (#c12f1f0, #1385a40, #ecac419, #e0ad836, #50acc32, #f122fdd)
- 🔄 **Update:** Updated setup.py (#c394c45, #b959c6a, #f2204bd, #2879782)
