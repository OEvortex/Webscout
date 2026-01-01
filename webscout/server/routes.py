"""
API routes for the Webscout server.
"""

import time
import uuid

from fastapi import Body, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from litprinter import ic
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from webscout.search.engines import ENGINES

from .config import AppConfig
from .exceptions import APIError
from .providers import (
    get_provider_instance,
    get_tti_provider_instance,
    resolve_provider_and_model,
    resolve_tti_provider_and_model,
)
from .request_models import ChatCompletionRequest, ImageGenerationRequest, ModelListResponse
from .request_processing import (
    handle_non_streaming_response,
    handle_streaming_response,
    prepare_provider_params,
    process_messages,
)


class Api:
    """API route handler class."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def register_validation_exception_handler(self):
        """Register comprehensive exception handlers."""
        from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

        from .exceptions import APIError

        github_footer = "If you believe this is a bug, please pull an issue at https://github.com/OEvortex/Webscout."

        @self.app.exception_handler(APIError)
        async def api_error_handler(request, exc: APIError):
            ic.configureOutput(prefix='ERROR| ')
            ic(f"API Error: {exc.message} (Status: {exc.status_code})")
            # Patch: add footer to error content before creating JSONResponse
            error_response = exc.to_response()
            # If the response is a JSONResponse, patch its content dict before returning
            if hasattr(error_response, 'body') and hasattr(error_response, 'media_type'):
                # Try to decode the body to dict and add footer if possible
                try:
                    import json
                    body_bytes = bytes(error_response.body) if hasattr(error_response, 'body') else b""
                    content_dict = json.loads(body_bytes.decode())
                    if "error" in content_dict:
                        content_dict["error"]["footer"] = github_footer
                        return JSONResponse(status_code=error_response.status_code, content=content_dict)
                except Exception:
                    pass
            return error_response

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request, exc: RequestValidationError):
            errors = exc.errors()
            error_messages = []
            body = await request.body()
            not body or body.strip() in (b"", b"null", b"{}")
            for error in errors:
                loc = error.get("loc", [])
                loc_str = " -> ".join(str(item) for item in loc)
                msg = error.get("msg", "Validation error")
                error_messages.append({
                    "loc": loc,
                    "message": f"{msg} at {loc_str}",
                    "type": error.get("type", "validation_error")
                })
            content = {
                "error": {
                    "message": "Request validation error.",
                    "details": error_messages,
                    "type": "validation_error",
                    "footer": github_footer
                }
            }
            return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=content)

        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request, exc: StarletteHTTPException):
            content = {
                "error": {
                    "message": exc.detail or "HTTP error occurred.",
                    "type": "http_error",
                    "footer": github_footer
                }
            }
            return JSONResponse(status_code=exc.status_code, content=content)

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc: Exception):
            ic.configureOutput(prefix='ERROR| ')
            ic(f"Unhandled server error: {exc}")
            content = {
                "error": {
                    "message": f"Internal server error: {str(exc)}",
                    "type": "server_error",
                    "footer": github_footer
                }
            }
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=content)

    def register_routes(self):
        """Register all API routes."""
        self._register_health_route()
        self._register_model_routes()
        self._register_chat_routes()
        self._register_websearch_routes()

    def _register_health_route(self):
        """Register health check route."""
        @self.app.get("/monitor/health", include_in_schema=False)
        async def health_check():
            """Health check endpoint for monitoring."""
            return {"status": "healthy", "service": "webscout-api", "version": "0.2.0"}

    def _register_model_routes(self):
        """Register model listing routes."""
        @self.app.get(
            "/v1/models",
            response_model=ModelListResponse,
            tags=["Chat Completions"],
            description="List all available chat completion models."
        )
        async def list_models():
            models = []
            for model_name, provider_class in AppConfig.provider_map.items():
                if "/" not in model_name:
                    continue  # Skip provider names
                if any(m["id"] == model_name for m in models):
                    continue
                models.append({
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": 'webscout'  # Set owned_by to webscout
                })
            # Sort models alphabetically by the part after the first '/'
            models = sorted(models, key=lambda m: m["id"].split("/", 1)[1].lower())
            return {
                "object": "list",
                "data": models
            }

        @self.app.get(
            "/v1/models/{model}",
            response_model=dict,
            tags=["Chat Completions"],
            description="Retrieve model instance details."
        )
        async def retrieve_model(model: str):
            """Retrieve model instance details."""
            try:
                # Check if model resolves to a valid provider/model pair
                resolve_provider_and_model(model)
                return {
                    "id": model,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "webscout"
                }
            except APIError:
                raise
            except Exception:
                 raise APIError(f"Model {model} not found", 404, "model_not_found", param="model")

        @self.app.get(
            "/v1/providers",
            tags=["Chat Completions"],
            description="Get details about available chat completion providers including supported models and parameters."
        )
        async def list_providers():
            """Get information about all available chat completion providers."""
            providers = {}

            # Extract unique provider names (exclude model mappings)
            provider_names = set()
            for key, provider_class in AppConfig.provider_map.items():
                if "/" not in key:  # Provider name, not model mapping
                    provider_names.add(key)

            for provider_name in sorted(provider_names):
                provider_class = AppConfig.provider_map[provider_name]

                # Get available models for this provider
                models = []
                for key, cls in AppConfig.provider_map.items():
                    if key.startswith(f"{provider_name}/"):
                        model_name = key.split("/", 1)[1]
                        models.append(model_name)

                # Sort models
                models = sorted(models)

                # Get supported parameters (common OpenAI-compatible parameters)
                supported_params = [
                    "model", "messages", "max_tokens", "temperature", "top_p",
                    "presence_penalty", "frequency_penalty", "stop", "stream", "user"
                ]

                providers[provider_name] = {
                    "name": provider_name,
                    "class": provider_class.__name__,
                    "models": models,
                    "parameters": supported_params,
                    "model_count": len(models)
                }

            return {
                "providers": providers,
                "total_providers": len(providers)
            }

        @self.app.get(
            "/v1/TTI/models",
            response_model=ModelListResponse,
            tags=["Image Generation"],
            description="List all available text-to-image (TTI) models."
        )
        async def list_tti_models():
            models = []
            for model_name, provider_class in AppConfig.tti_provider_map.items():
                if "/" not in model_name:
                    continue  # Skip provider names
                if any(m["id"] == model_name for m in models):
                    continue
                models.append({
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": 'webscout'  # Set owned_by to webscout
                })
            # Sort models alphabetically by the part after the first '/'
            models = sorted(models, key=lambda m: m["id"].split("/", 1)[1].lower())
            return {
                "object": "list",
                "data": models
            }

        @self.app.get(
            "/v1/TTI/providers",
            tags=["Image Generation"],
            description="Get details about available text-to-image (TTI) providers including supported models and parameters."
        )
        async def list_tti_providers():
            """Get information about all available TTI providers."""
            providers = {}

            # Extract unique provider names (exclude model mappings)
            provider_names = set()
            for key, provider_class in AppConfig.tti_provider_map.items():
                if "/" not in key:  # Provider name, not model mapping
                    provider_names.add(key)

            for provider_name in sorted(provider_names):
                provider_class = AppConfig.tti_provider_map[provider_name]

                # Get available models for this provider
                models = []
                for key, cls in AppConfig.tti_provider_map.items():
                    if key.startswith(f"{provider_name}/"):
                        model_name = key.split("/", 1)[1]
                        models.append(model_name)

                # Sort models
                models = sorted(models)

                # Get supported parameters (common TTI parameters)
                supported_params = [
                    "prompt", "model", "n", "size", "response_format", "user",
                    "style", "aspect_ratio", "timeout", "image_format", "seed"
                ]

                providers[provider_name] = {
                    "name": provider_name,
                    "class": provider_class.__name__,
                    "models": models,
                    "parameters": supported_params,
                    "model_count": len(models)
                }

            return {
                "providers": providers,
                "total_providers": len(providers)
            }

    def _register_chat_routes(self):
        """Register chat completion routes."""
        @self.app.post(
            "/v1/chat/completions",
            response_model_exclude_none=True,
            response_model_exclude_unset=True,
            tags=["Chat Completions"],
            description="Generate chat completions using the specified model.",
            openapi_extra={
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChatCompletionRequest"
                            },
                            "example": ChatCompletionRequest.Config.schema_extra["example"]
                        }
                    }
                }
            }
        )
        async def chat_completions(
            request: Request,
            chat_request: ChatCompletionRequest = Body(...)
        ):
            """Handle chat completion requests with comprehensive error handling."""
            start_time = time.time()
            request_id = f"chatcmpl-{uuid.uuid4()}"

            try:
                ic.configureOutput(prefix='INFO| ')
                ic(f"Processing chat completion request {request_id} for model: {chat_request.model}")

                # Resolve provider and model
                provider_class, model_name = resolve_provider_and_model(chat_request.model)

                # Initialize provider with caching and error handling
                try:
                    provider = get_provider_instance(provider_class)
                    ic.configureOutput(prefix='DEBUG| ')
                    ic(f"Using provider instance: {provider_class.__name__}")
                except Exception as e:
                    ic.configureOutput(prefix='ERROR| ')
                    ic(f"Failed to initialize provider {provider_class.__name__}: {e}")
                    raise APIError(
                        f"Failed to initialize provider {provider_class.__name__}: {e}",
                        HTTP_500_INTERNAL_SERVER_ERROR,
                        "provider_error"
                    )

                # Process and validate messages
                processed_messages = process_messages(chat_request.messages)

                # Prepare parameters for provider
                params = prepare_provider_params(chat_request, model_name, processed_messages)

                # Extract client IP address
                client_ip = request.client.host if request.client else "unknown"
                if "x-forwarded-for" in request.headers:
                    client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
                elif "x-real-ip" in request.headers:
                    client_ip = request.headers["x-real-ip"]

                # Extract question from messages (last user message)
                question = ""
                for msg in reversed(processed_messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            question = content
                        elif isinstance(content, list) and content:
                            # Handle content with multiple parts (text, images, etc.)
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    question = part.get("text", "")
                                    break
                        break

                # Handle streaming vs non-streaming
                if chat_request.stream:
                    return await handle_streaming_response(
                        provider, params, request_id, client_ip, question, model_name, start_time,
                        provider_class.__name__, request
                    )
                else:
                    return await handle_non_streaming_response(
                        provider, params, request_id, start_time, client_ip, question, model_name,
                        provider_class.__name__, request
                    )

            except APIError:
                # Re-raise API errors as-is
                raise
            except Exception as e:
                ic.configureOutput(prefix='ERROR| ')
                ic(f"Unexpected error in chat completion {request_id}: {e}")
                raise APIError(
                    f"Internal server error: {str(e)}",
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "internal_error"
                )


        @self.app.post(
            "/v1/images/generations",
            tags=["Image Generation"],
            description="Generate images from text prompts using the specified TTI model."
        )
        async def image_generations(
            image_request: ImageGenerationRequest = Body(...)
        ):
            """Handle image generation requests."""
            start_time = time.time()
            request_id = f"img-{uuid.uuid4()}"

            try:
                ic.configureOutput(prefix='INFO| ')
                ic(f"Processing image generation request {request_id} for model: {image_request.model}")

                # Resolve TTI provider and model
                provider_class, model_name = resolve_tti_provider_and_model(image_request.model)

                # Initialize TTI provider
                try:
                    provider = get_tti_provider_instance(provider_class)
                    ic.configureOutput(prefix='DEBUG| ')
                    ic(f"Using TTI provider instance: {provider_class.__name__}")
                except APIError as e:
                    # Add helpful footer for provider errors
                    return JSONResponse(
                        status_code=e.status_code,
                        content={
                            "error": {
                                "message": e.message,
                                "type": e.error_type,
                                "footer": "If you believe this is a bug, please pull an issue at https://github.com/OEvortex/Webscout."
                            }
                        }
                    )
                except Exception as e:
                    ic.configureOutput(prefix='ERROR| ')
                    ic(f"Failed to initialize TTI provider {provider_class.__name__}: {e}")
                    raise APIError(
                        f"Failed to initialize TTI provider {provider_class.__name__}: {e}",
                        HTTP_500_INTERNAL_SERVER_ERROR,
                        "provider_error"
                    )

                # Prepare parameters for TTI provider
                params = {
                    "prompt": image_request.prompt,
                    "model": model_name,
                    "n": image_request.n,
                    "size": image_request.size,
                    "response_format": image_request.response_format,
                }

                # Add optional parameters
                optional_params = ["user", "style", "aspect_ratio", "timeout", "image_format", "seed"]
                for param in optional_params:
                    value = getattr(image_request, param, None)
                    if value is not None:
                        params[param] = value

                # Generate images
                response = provider.images.create(**params)

                # Standardize response format
                if hasattr(response, "model_dump"):
                    response_data = response.model_dump(exclude_none=True)
                elif hasattr(response, "dict"):
                    response_data = response.dict(exclude_none=True)
                elif isinstance(response, dict):
                    response_data = response
                else:
                    raise APIError(
                        "Invalid response format from TTI provider",
                        HTTP_500_INTERNAL_SERVER_ERROR,
                        "provider_error"
                    )

                elapsed = time.time() - start_time
                ic.configureOutput(prefix='INFO| ')
                ic(f"Completed image generation request {request_id} in {elapsed:.2f}s")

                return response_data
            except APIError:
                raise
            except Exception as e:
                ic.configureOutput(prefix='ERROR| ')
                ic(f"Unexpected error in image generation {request_id}: {e}")
                raise APIError(
                    f"Internal server error: {str(e)}",
                    HTTP_500_INTERNAL_SERVER_ERROR,
                    "internal_error"
                )



    def _register_websearch_routes(self):
        """Register web search endpoint."""

        @self.app.get(
            "/search",
            tags=["Web search"],
            description="Unified web search endpoint supporting all available search engines with various search types including text, news, images, suggestions, answers, maps, translate, and weather."
        )
        async def websearch(
            q: str = Query(..., description="Search query"),
            engine: str = Query("duckduckgo", description=f"Search engine: {', '.join(sorted(set(name for cat in ENGINES.values() for name in cat)))}"),
            max_results: int = Query(10, description="Maximum number of results"),
            region: str = Query("all", description="Region code (optional)"),
            safesearch: str = Query("moderate", description="Safe search: on, moderate, off"),
            type: str = Query("text", description="Search type: text, news, images, videos, suggestions, answers, maps, translate, weather"),
            place: str = Query(None, description="Place for maps search"),
            street: str = Query(None, description="Street for maps search"),
            city: str = Query(None, description="City for maps search"),
            county: str = Query(None, description="County for maps search"),
            state: str = Query(None, description="State for maps search"),
            country: str = Query(None, description="Country for maps search"),
            postalcode: str = Query(None, description="Postal code for maps search"),
            latitude: str = Query(None, description="Latitude for maps search"),
            longitude: str = Query(None, description="Longitude for maps search"),
            radius: int = Query(0, description="Radius for maps search"),
            from_: str = Query(None, description="Source language for translate"),
            to: str = Query("en", description="Target language for translate"),
            language: str = Query("en", description="Language for weather"),
        ):
            """Unified web search endpoint."""
            github_footer = "If you believe this is a bug, please pull an issue at https://github.com/pyscout/Webscout."
            try:
                # Dynamically support all engines in ENGINES
                found = False
                for category, engines in ENGINES.items():
                    if engine in engines:
                        found = True
                        engine_cls = engines[engine]
                        searcher = engine_cls()
                        # Try to call the appropriate method based on 'type'
                        if hasattr(searcher, "run"):
                            method = getattr(searcher, "run")
                            # Some engines may require different params
                            try:
                                if type in ("text", "images", "news", "videos"):
                                    results = method(keywords=q, region=region, safesearch=safesearch, max_results=max_results)
                                elif type == "suggestions":
                                    results = method(q, region=region)
                                elif type == "answers":
                                    results = method(keywords=q)
                                elif type == "maps":
                                    results = method(keywords=q, place=place, street=street, city=city, county=county, state=state, country=country, postalcode=postalcode, latitude=latitude, longitude=longitude, radius=radius, max_results=max_results)
                                elif type == "translate":
                                    results = method(keywords=q, from_=from_, to=to)
                                elif type == "weather":
                                    results = method(location=q, language=language)
                                else:
                                    return {"error": f"{engine} does not support type '{type}'.", "footer": github_footer}
                                # Try to serialize results if needed
                                if isinstance(results, list) and results and hasattr(results[0], "__dict__"):
                                    results = [r.__dict__ for r in results]
                                return {"engine": engine, "type": type, "results": results}
                            except Exception as ex:
                                return {"error": f"Error running {engine}.{type}: {ex}", "footer": github_footer}
                        else:
                            return {"error": f"{engine} does not support type '{type}'.", "footer": github_footer}
                if not found:
                    return {"error": f"Unknown engine. Use one of: {', '.join(sorted(set(name for cat in ENGINES.values() for name in cat)))}.", "footer": github_footer}
            except Exception as e:
                # Special handling for rate limit errors
                msg = str(e)
                if "429" in msg or "rate limit" in msg.lower():
                    return {
                        "error": "You have hit the search rate limit. Please try again later.",
                        "details": msg,
                        "code": 429,
                        "footer": github_footer
                    }
                return {
                    "error": f"Search request failed: {msg}",
                    "footer": github_footer
                }

        @self.app.get(
            "/search/provider",
            tags=["Web search"],
            description="Get details about available search providers including supported categories and parameters."
        )
        async def get_search_providers():
            """Get information about all available search providers."""
            providers = {}

            # Collect all unique engine names
            all_engines = set()
            for category_engines in ENGINES.values():
                all_engines.update(category_engines.keys())

            for engine_name in sorted(all_engines):
                # Find all categories this engine supports
                categories = []
                for category, engines in ENGINES.items():
                    if engine_name in engines:
                        categories.append(category)

                # Get supported parameters based on categories
                supported_params = ["q"]  # query is always supported

                if "text" in categories or "images" in categories or "news" in categories or "videos" in categories:
                    supported_params.extend(["max_results", "region", "safesearch"])

                if "suggestions" in categories:
                    supported_params.extend(["region"])

                if "maps" in categories:
                    supported_params.extend(["place", "street", "city", "county", "state", "country", "postalcode", "latitude", "longitude", "radius", "max_results"])

                if "translate" in categories:
                    supported_params.extend(["from_", "to"])

                if "weather" in categories:
                    supported_params.extend(["language"])

                # Remove duplicates
                supported_params = list(set(supported_params))

                providers[engine_name] = {
                    "name": engine_name,
                    "categories": sorted(categories),
                    "supported_types": sorted(categories),  # types are the same as categories
                    "parameters": sorted(supported_params)
                }

            return {
                "providers": providers,
                "total_providers": len(providers)
            }
