# Tech Stack - Webscout

## Core Languages
- **Python (>= 3.9):** The primary language for the entire toolkit, chosen for its vast library ecosystem and dominance in AI and scripting.

## Frameworks & Libraries
- **Asynchronous Programming:** `asyncio` and `aiohttp` are used for high-performance, non-blocking network requests and file operations.
- **API Server:** `FastAPI` provides a high-performance, easy-to-use framework for the OpenAI-compatible API server, with `pydantic` for data validation and `uvicorn` as the ASGI server.
- **Web Scraping & Crawling:** A robust suite including `lxml` for fast parsing, `nodriver` for browser automation, and `curl_cffi` for bypassing anti-bot measures.
- **AI Integration:** Direct integration with major AI SDKs like `google-generativeai` and `openai`, alongside a massive collection of custom, reverse-engineered providers.
- **CLI & UX:** `rich` and `litprinter` are used to create beautiful, informative, and modern command-line interfaces.
- **System Utilities:** `psutil` for system monitoring and `aiofiles` for async I/O.

## Data & Media
- **Serialization:** `orjson` for high-speed JSON processing and `PyYAML` for configuration management.
- **Image Handling:** `Pillow` for image processing tasks related to TTI (Text-to-Image) features.

## Development & Quality Assurance
- **Linting & Formatting:** `ruff` is used for extremely fast linting and code formatting, ensuring consistent code style.
- **Testing:** `pytest` is the standard framework for unit and integration testing.
- **Package Management:** `pip` and `uv` are supported for dependency management and project execution.
