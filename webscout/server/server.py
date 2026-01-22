"""
Webscout OpenAI-Compatible API Server

A FastAPI-based server that provides OpenAI-compatible endpoints for various LLM providers.
Supports streaming and non-streaming chat completions with comprehensive error handling,
authentication, and provider management.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse

from .config import AppConfig, ServerConfig
from .providers import initialize_provider_map, initialize_tti_provider_map
from .routes import Api
from .ui_templates import LANDING_PAGE_HTML, SWAGGER_CSS

# Configuration constants
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"
API_VERSION = "v1"

# Setup logging
# Using litprinter console instead of standard logging

# Global configuration instance - lazy initialization
config = None


def get_config() -> ServerConfig:
    """Get or create the global configuration instance."""
    global config
    if config is None:
        config = ServerConfig()
    return config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    if hasattr(app.state, "startup_event"):
        await app.state.startup_event()
    yield
    # Shutdown (if needed in the future)


def create_app():
    """Create and configure the FastAPI application."""
    app_title = os.getenv("WEBSCOUT_API_TITLE", "Webscout API")
    app_description = os.getenv(
        "WEBSCOUT_API_DESCRIPTION", "OpenAI API compatible interface for various LLM providers"
    )
    app_version = os.getenv("WEBSCOUT_API_VERSION", "0.2.0")
    app_docs_url = os.getenv("WEBSCOUT_API_DOCS_URL", "/docs")
    app_redoc_url = os.getenv("WEBSCOUT_API_REDOC_URL", "/redoc")
    app_openapi_url = os.getenv("WEBSCOUT_API_OPENAPI_URL", "/openapi.json")

    app = FastAPI(
        title=app_title,
        description=app_description,
        version=app_version,
        docs_url=None,  # Disable default docs
        redoc_url=app_redoc_url,
        openapi_url=app_openapi_url,
        lifespan=lifespan,
    )

    # Simple Custom Swagger UI with WebScout footer
    @app.get(app_docs_url, include_in_schema=False)
    async def custom_swagger_ui_html():
        openapi_url = app.openapi_url or "/openapi.json"
        swagger_response = get_swagger_ui_html(
            openapi_url=openapi_url,
            title=app.title + " - API Documentation",
        )
        html = bytes(swagger_response.body).decode("utf-8")

        # Custom footer and styles
        footer_html = """
        <div class="webscout-footer">
            Powered by <a href='https://github.com/OEvortex/Webscout' target='_blank'>WebScout</a>
        </div>
        """

        # Inject custom CSS and footer
        html = html.replace("</head>", f"<style>{SWAGGER_CSS}</style></head>")
        html = html.replace("</body>", f"{footer_html}</body>")
        return HTMLResponse(content=html)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize API routes
    api = Api(app)
    api.register_validation_exception_handler()
    api.register_routes()

    # Initialize providers
    initialize_provider_map()
    initialize_tti_provider_map()

    # Root landing page
    @app.get("/", include_in_schema=False)
    async def root():
        return HTMLResponse(content=LANDING_PAGE_HTML)

    return app


def create_app_debug():
    """Create app in debug mode."""
    return create_app()


def start_server(
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
    default_provider: Optional[str] = None,
    base_url: Optional[str] = None,
    workers: int = 1,
    log_level: str = "info",
    debug: bool = False,
):
    """Start the API server with the given configuration."""
    run_api(
        host=host,
        port=port,
        default_provider=default_provider,
        base_url=base_url,
        workers=workers,
        log_level=log_level,
        debug=debug,
    )


def run_api(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    default_provider: Optional[str] = None,
    base_url: Optional[str] = None,
    debug: bool = False,
    workers: int = 1,
    log_level: str = "info",
    show_available_providers: bool = True,
) -> None:
    """Run the API server with configuration."""
    print("Starting Webscout OpenAI API server...")
    if port is None:
        port = DEFAULT_PORT

    AppConfig.set_config(
        api_key=None,
        default_provider=default_provider or AppConfig.default_provider,
        base_url=base_url,
        auth_required=False,
        rate_limit_enabled=False,
    )

    if show_available_providers:
        if not AppConfig.provider_map:
            initialize_provider_map()
        if not AppConfig.tti_provider_map:
            initialize_tti_provider_map()

        print("\n=== Webscout OpenAI API Server ===")
        print(f"Server URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        if AppConfig.base_url:
            print(f"Base Path: {AppConfig.base_url}")
            api_endpoint_base = (
                f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}{AppConfig.base_url}"
            )
        else:
            api_endpoint_base = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"

        print(f"API Endpoint: {api_endpoint_base}/v1/chat/completions")
        print(f"Docs URL: {api_endpoint_base}/docs")

        # Show authentication status
        print("Authentication: 🔓 DISABLED")

        # Show rate limiting status
        print("Rate Limiting: ⚡ DISABLED")

        print(f"Default Provider: {AppConfig.default_provider}")
        print(f"Workers: {workers}")
        print(f"Log Level: {log_level}")
        print(f"Debug Mode: {'Enabled' if debug else 'Disabled'}")

        providers = list(set(v.__name__ for v in AppConfig.provider_map.values()))
        print(f"\n--- Available Providers ({len(providers)}) ---")
        for i, provider_name in enumerate(sorted(providers), 1):
            print(f"{i}. {provider_name}")

        provider_class_names = set(v.__name__ for v in AppConfig.provider_map.values())
        models = sorted(
            [model for model in AppConfig.provider_map.keys() if model not in provider_class_names]
        )
        if models:
            print(f"\n--- Available Models ({len(models)}) ---")
            for i, model_name in enumerate(models, 1):
                print(f"{i}. {model_name} (via {AppConfig.provider_map[model_name].__name__})")
        else:
            print("\nNo specific models registered. Use provider names as models.")

        tti_providers = list(set(v.__name__ for v in AppConfig.tti_provider_map.values()))
        print(f"\n--- Available TTI Providers ({len(tti_providers)}) ---")
        for i, provider_name in enumerate(sorted(tti_providers), 1):
            print(f"{i}. {provider_name}")

        tti_models = sorted(
            [model for model in AppConfig.tti_provider_map.keys() if model not in tti_providers]
        )
        if tti_models:
            print(f"\n--- Available TTI Models ({len(tti_models)}) ---")
            for i, model_name in enumerate(tti_models, 1):
                print(f"{i}. {model_name} (via {AppConfig.tti_provider_map[model_name].__name__})")
        else:
            print("\nNo specific TTI models registered. Use TTI provider names as models.")

        print("\nUse Ctrl+C to stop the server.")
        print("=" * 40 + "\n")

    uvicorn_app_str = (
        "webscout.server.server:create_app_debug" if debug else "webscout.server.server:create_app"
    )

    # Configure uvicorn settings
    log_level_str: str = log_level.lower() if log_level else ("debug" if debug else "info")
    port_int: int = int(port)

    # Add workers only if not in debug mode
    if not debug and workers > 1:
        print(f"Starting with {workers} workers...")
        uvicorn.run(
            app=uvicorn_app_str,
            host=host,
            port=port_int,
            factory=True,
            reload=debug,
            log_level=log_level_str,
            workers=workers,
        )
    elif debug:
        print("Debug mode enabled - using single worker with reload...")
        uvicorn.run(
            app=uvicorn_app_str,
            host=host,
            port=port_int,
            factory=True,
            reload=debug,
            log_level=log_level_str,
        )
    else:
        # Single worker in production mode
        uvicorn.run(
            app=uvicorn_app_str,
            host=host,
            port=port_int,
            factory=True,
            reload=debug,
            log_level=log_level_str,
            workers=1,
        )


def main():
    """Main entry point for the webscout-server console script."""
    import argparse

    # Read environment variables with fallbacks
    default_port = int(os.getenv("WEBSCOUT_PORT", os.getenv("PORT", DEFAULT_PORT)))
    default_host = os.getenv("WEBSCOUT_HOST", DEFAULT_HOST)
    default_workers = int(os.getenv("WEBSCOUT_WORKERS", "1"))
    default_log_level = os.getenv("WEBSCOUT_LOG_LEVEL", "info")
    default_provider = os.getenv("WEBSCOUT_DEFAULT_PROVIDER", os.getenv("DEFAULT_PROVIDER"))
    default_base_url = os.getenv("WEBSCOUT_BASE_URL", os.getenv("BASE_URL"))
    default_debug = os.getenv("WEBSCOUT_DEBUG", os.getenv("DEBUG", "false")).lower() == "true"

    parser = argparse.ArgumentParser(description="Start Webscout OpenAI-compatible API server")
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to run the server on (default: {default_port})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=default_host,
        help=f"Host to bind the server to (default: {default_host})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers,
        help=f"Number of worker processes (default: {default_workers})",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=default_log_level,
        choices=["debug", "info", "warning", "error", "critical"],
        help=f"Log level (default: {default_log_level})",
    )
    parser.add_argument(
        "--default-provider",
        type=str,
        default=default_provider,
        help="Default provider to use (optional)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=default_base_url,
        help="Base URL for the API (optional, e.g., /api/v1)",
    )
    parser.add_argument(
        "--debug", action="store_true", default=default_debug, help="Run in debug mode"
    )
    args = parser.parse_args()

    # Print configuration summary
    print("Configuration:")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Workers: {args.workers}")
    print(f"  Log Level: {args.log_level}")
    print(f"  Debug Mode: {args.debug}")
    print("  Authentication: 🔓 DISABLED")
    print("  Rate Limiting: ⚡ DISABLED")
    print(f"  Default Provider: {args.default_provider or 'Not set'}")
    print(f"  Base URL: {args.base_url or 'Not set'}")
    print()

    run_api(
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level=args.log_level,
        default_provider=args.default_provider,
        base_url=args.base_url,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
