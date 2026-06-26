"""
Request processing utilities for the LLM4Free API.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse
from litprinter import ic
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR

from llm4free.llm.utils import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
    CompletionUsage,
)

# from .simple_logger import log_api_request, get_client_ip, generate_request_id
from .config import AppConfig
from .exceptions import APIError, clean_text
from .request_models import (
    ChatCompletionRequest,
    Message,
    AnthropicMessagesRequest,
    AnthropicMessage,
    AnthropicTextBlock,
    AnthropicImageBlock,
    AnthropicToolUseBlock,
    AnthropicToolResultBlock,
    AnthropicToolDefinition,
    AnthropicToolChoice,
    AnthropicMessagesResponse,
    AnthropicTextResponseBlock,
    AnthropicToolUseResponseBlock,
    AnthropicUsage,
)


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return getattr(request.client, "host", "unknown")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


async def log_api_request(
    request_id: str,
    ip_address: str,
    model: str,
    question: str,
    answer: str,
    **kwargs
) -> bool:
    """Convenience function to log API requests."""
    ic(f"Request {request_id}: model={model}, ip={ip_address}")
    return True


async def log_request(request_id: str, ip_address: str, model_used: str, question: str,
                     answer: str, response_time_ms: int, status_code: int = 200,
                     error_message: Optional[str] = None, provider: Optional[str] = None, request_obj=None):
    """Log API request."""
    try:
        # Use simple logger if request logging is enabled
        if AppConfig.request_logging_enabled:
            user_agent = None
            if request_obj:
                user_agent = request_obj.headers.get("user-agent")

            await log_api_request(
                request_id=request_id,
                ip_address=ip_address,
                model=model_used,
                question=question,
                answer=answer,
                provider=provider,
                processing_time_ms=response_time_ms,
                error=error_message,
                user_agent=user_agent
            )
    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Failed to log request {request_id}: {e}")
        # Don't raise exception to avoid breaking the main request flow


def process_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Process and validate chat messages."""
    processed_messages = []

    for i, msg_in in enumerate(messages):
        try:
            message_dict_out: Dict[str, Any] = {"role": msg_in.role}

            if msg_in.content is None:
                message_dict_out["content"] = None
            elif isinstance(msg_in.content, str):
                message_dict_out["content"] = msg_in.content
            else:  # List[MessageContentParts]
                message_dict_out["content"] = [
                    part.model_dump(exclude_none=True) for part in msg_in.content
                ]

            if msg_in.name:
                message_dict_out["name"] = msg_in.name

            # Add tool call fields
            if msg_in.tool_calls is not None:
                message_dict_out["tool_calls"] = msg_in.tool_calls

            if msg_in.tool_call_id is not None:
                message_dict_out["tool_call_id"] = msg_in.tool_call_id

            processed_messages.append(message_dict_out)

        except Exception as e:
            raise APIError(
                f"Invalid message at index {i}: {str(e)}",
                HTTP_422_UNPROCESSABLE_CONTENT,
                "invalid_request_error",
                param=f"messages[{i}]"
            )

    return processed_messages


def prepare_provider_params(chat_request: ChatCompletionRequest, model_name: str,
                          processed_messages: List[Dict[str, Any]],
                          provider_name: Optional[str] = None) -> Dict[str, Any]:
    """Prepare parameters for the provider."""
    provider_name_normalized = provider_name or ""

    def normalize_text_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize message content to plain text for text-only providers."""
        normalized_messages: List[Dict[str, Any]] = []

        for message in messages:
            normalized_message = dict(message)
            content = normalized_message.get("content")

            if content is None:
                normalized_message["content"] = ""
            elif isinstance(content, str):
                normalized_message["content"] = content
            elif isinstance(content, list):
                text_parts: List[str] = []
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        if isinstance(part.get("text"), str):
                            text_parts.append(part["text"])
                normalized_message["content"] = "".join(text_parts)
            elif isinstance(content, dict) and isinstance(content.get("text"), str):
                normalized_message["content"] = content["text"]
            else:
                normalized_message["content"] = str(content)

            normalized_messages.append(normalized_message)

        return normalized_messages

    use_text_only_compat = provider_name_normalized in {"Toolbaz", "TypliAI"}
    messages = normalize_text_messages(processed_messages) if use_text_only_compat else processed_messages

    params = {
        "model": model_name,
        "messages": messages,
        "stream": bool(chat_request.stream),
    }

    # Add optional parameters if present
    optional_params = (
        ["temperature", "max_tokens", "top_p"]
        if use_text_only_compat
        else [
            "temperature",
            "max_tokens",
            "top_p",
            "presence_penalty",
            "frequency_penalty",
            "stop",
            "user",
        ]
    )

    for param in optional_params:
        value = getattr(chat_request, param, None)
        if value is not None:
            params[param] = value

    # Add tool calling parameters
    tool_params = ["tools", "tool_choice", "parallel_tool_calls"]
    for param in tool_params:
        value = getattr(chat_request, param, None)
        if value is not None:
            params[param] = value

    # Add deprecated tool calling parameters (for backward compatibility)
    deprecated_tool_params = ["functions", "function_call"]
    for param in deprecated_tool_params:
        value = getattr(chat_request, param, None)
        if value is not None:
            params[param] = value

    return params


async def handle_streaming_response(provider: Any, params: Dict[str, Any], request_id: str,
                                  ip_address: str, question: str, model_name: str, start_time: float,
                                  provider_name: Optional[str] = None, request_obj=None) -> StreamingResponse:
    """Handle streaming chat completion response."""
    collected_content = []

    async def streaming():
        nonlocal collected_content
        try:
            ic.configureOutput(prefix='DEBUG| ')
            ic(f"Starting streaming response for request {request_id}")
            completion_stream = provider.chat.completions.create(**params)

            # Check if it's iterable (generator, iterator, or other iterable types)
            if hasattr(completion_stream, '__iter__') and not isinstance(completion_stream, (str, bytes, dict)):
                try:
                    for chunk in completion_stream:
                        # Standardize chunk format before sending
                        model_dump = getattr(chunk, 'model_dump', None)
                        model_dict = getattr(chunk, 'dict', None)
                        if model_dump and callable(model_dump):  # Pydantic v2
                            chunk_data = model_dump(exclude_none=True)
                        elif model_dict and callable(model_dict):  # Pydantic v1
                            chunk_data = model_dict(exclude_none=True)
                        elif isinstance(chunk, dict):
                            chunk_data = chunk
                        else:
                            chunk_data = chunk

                        # Clean text content in the chunk to remove control characters
                        if isinstance(chunk_data, dict) and 'choices' in chunk_data:
                            for choice in chunk_data.get('choices', []):
                                if isinstance(choice, dict):
                                    # Handle delta for streaming
                                    if 'delta' in choice and isinstance(choice['delta'], dict) and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        if content:
                                            collected_content.append(content)
                                        choice['delta']['content'] = clean_text(content)
                                    # Handle message for non-streaming
                                    elif 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
                                        content = choice['message']['content']
                                        if content:
                                            collected_content.append(content)
                                        choice['message']['content'] = clean_text(content)

                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                except TypeError as te:
                    ic.configureOutput(prefix='ERROR| ')
                    ic(f"Error iterating over completion_stream: {te}")
                    # Fall back to treating as non-generator response
                    model_dump = getattr(completion_stream, 'model_dump', None)
                    model_dict = getattr(completion_stream, 'dict', None)
                    if model_dump and callable(model_dump):
                        response_data = model_dump(exclude_none=True)
                    elif model_dict and callable(model_dict):
                        response_data = model_dict(exclude_none=True)
                    else:
                        response_data = completion_stream

                    # Clean text content in the response
                    if isinstance(response_data, dict) and 'choices' in response_data:
                        for choice in response_data.get('choices', []):
                            if isinstance(choice, dict):
                                if 'delta' in choice and isinstance(choice['delta'], dict) and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                    if content:
                                        collected_content.append(content)
                                    choice['delta']['content'] = clean_text(content)
                                elif 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
                                    content = choice['message']['content']
                                    if content:
                                        collected_content.append(content)
                                    choice['message']['content'] = clean_text(content)

                    yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            else:  # Non-generator response
                model_dump = getattr(completion_stream, 'model_dump', None)
                model_dict = getattr(completion_stream, 'dict', None)
                if model_dump and callable(model_dump):
                    response_data = model_dump(exclude_none=True)
                elif model_dict and callable(model_dict):
                    response_data = model_dict(exclude_none=True)
                else:
                    response_data = completion_stream

                # Clean text content in the response
                if isinstance(response_data, dict) and 'choices' in response_data:
                    for choice in response_data.get('choices', []):
                        if isinstance(choice, dict):
                            if 'delta' in choice and isinstance(choice['delta'], dict) and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    collected_content.append(content)
                                choice['delta']['content'] = clean_text(content)
                            elif 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
                                content = choice['message']['content']
                                if content:
                                    collected_content.append(content)
                                choice['message']['content'] = clean_text(content)

                yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            ic.configureOutput(prefix='ERROR| ')
            ic(f"Error in streaming response for request {request_id}: {e}")
            error_message = clean_text(str(e))
            error_data = {
                "error": {
                    "message": error_message,
                    "type": "server_error",
                    "code": "streaming_error"
                }
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

            # Log error request
            response_time_ms = int((time.time() - start_time) * 1000)
            await log_request(
                request_id=request_id,
                ip_address=ip_address,
                model_used=model_name,
                question=question,
                answer="",
                response_time_ms=response_time_ms,
                status_code=500,
                error_message=error_message,
                provider=provider_name,
                request_obj=request_obj
            )
        finally:
            yield "data: [DONE]\n\n"

            # Log successful streaming request
            if collected_content:
                answer = "".join(collected_content)
                response_time_ms = int((time.time() - start_time) * 1000)
                await log_request(
                    request_id=request_id,
                    ip_address=ip_address,
                    model_used=model_name,
                    question=question,
                    answer=answer,
                    response_time_ms=response_time_ms,
                    status_code=200,
                    provider=provider_name,
                    request_obj=request_obj
                )

    return StreamingResponse(streaming(), media_type="text/event-stream")


async def handle_non_streaming_response(provider: Any, params: Dict[str, Any],
                                      request_id: str, start_time: float, ip_address: str,
                                      question: str, model_name: str, provider_name: Optional[str] = None,
                                      request_obj=None) -> Dict[str, Any]:
    """Handle non-streaming chat completion response."""
    try:
        ic.configureOutput(prefix='DEBUG| ')
        ic(f"Starting non-streaming response for request {request_id}")
        completion = provider.chat.completions.create(**params)

        if completion is None:
            # Return a valid OpenAI-compatible error response
            error_response = ChatCompletion(
                id=request_id,
                created=int(time.time()),
                model=params.get("model", "unknown"),
                choices=[Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="No response generated."),
                    finish_reason="error"
                )],
                usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
            ).model_dump(exclude_none=True)

            # Log error request
            response_time_ms = int((time.time() - start_time) * 1000)
            await log_request(
                request_id=request_id,
                ip_address=ip_address,
                model_used=model_name,
                question=question,
                answer="No response generated.",
                response_time_ms=response_time_ms,
                status_code=500,
                error_message="No response generated from provider",
                provider=provider_name,
                request_obj=request_obj
            )

            return error_response

        # Standardize response format
        if hasattr(completion, "model_dump"):  # Pydantic v2
            response_data = completion.model_dump(exclude_none=True)
        elif hasattr(completion, "dict"):  # Pydantic v1
            response_data = completion.dict(exclude_none=True)
        elif isinstance(completion, dict):
            response_data = completion
        else:
            raise APIError(
                "Invalid response format from provider",
                HTTP_500_INTERNAL_SERVER_ERROR,
                "provider_error"
            )

        # Extract answer from response and clean text content
        answer = ""
        if isinstance(response_data, dict) and 'choices' in response_data:
            for choice in response_data.get('choices', []):
                if isinstance(choice, dict) and 'message' in choice:
                    if isinstance(choice['message'], dict) and 'content' in choice['message']:
                        content = choice['message']['content']
                        if content:
                            answer = content
                        choice['message']['content'] = clean_text(content)

        elapsed = time.time() - start_time
        response_time_ms = int(elapsed * 1000)
        ic.configureOutput(prefix='INFO| ')
        ic(f"Completed non-streaming request {request_id} in {elapsed:.2f}s")

        # Log successful request
        await log_request(
            request_id=request_id,
            ip_address=ip_address,
            model_used=model_name,
            question=question,
            answer=answer,
            response_time_ms=response_time_ms,
            status_code=200,
            provider=provider_name,
            request_obj=request_obj
        )

        return response_data

    except Exception as e:
        ic.configureOutput(prefix='ERROR| ')
        ic(f"Error in non-streaming response for request {request_id}: {e}")
        error_message = clean_text(str(e))

        # Log error request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_request(
            request_id=request_id,
            ip_address=ip_address,
            model_used=model_name,
            question=question,
            answer="",
            response_time_ms=response_time_ms,
            status_code=500,
            error_message=error_message,
            provider=provider_name,
            request_obj=request_obj
        )

        raise APIError(
            f"Provider error: {error_message}",
            HTTP_500_INTERNAL_SERVER_ERROR,
            "provider_error"
        )


# ============================================================================
# Anthropic API Conversion Functions
# ============================================================================

def extract_system_from_messages(messages: List[Dict[str, Any]]) -> Optional[str]:
    """Extract system message content from OpenAI-style messages array."""
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                return "".join(text_parts)
    return None


def convert_anthropic_to_openai(anthropic_request: AnthropicMessagesRequest) -> Dict[str, Any]:
    """Convert Anthropic Messages request to OpenAI Chat Completion format."""
    messages = []

    # Add system message if present (Anthropic uses top-level system param)
    if anthropic_request.system:
        if isinstance(anthropic_request.system, str):
            messages.append({"role": "system", "content": anthropic_request.system})
        elif isinstance(anthropic_request.system, list):
            text_parts = []
            for block in anthropic_request.system:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            if text_parts:
                messages.append({"role": "system", "content": "".join(text_parts)})

    # Convert messages
    for msg in anthropic_request.messages:
        openai_msg: Dict[str, Any] = {"role": msg.role}

        if isinstance(msg.content, str):
            openai_msg["content"] = msg.content
        elif isinstance(msg.content, list):
            # Check if it's simple text content
            if len(msg.content) == 1 and hasattr(msg.content[0], "text"):
                openai_msg["content"] = msg.content[0].text
            else:
                # Handle multimodal/tool content
                openai_content = []
                tool_calls = []
                tool_results = []

                for block in msg.content:
                    if hasattr(block, "type"):
                        if block.type == "text":
                            openai_content.append({"type": "text", "text": block.text})
                        elif block.type == "image" and hasattr(block, "source"):
                            if block.source.type == "url" and block.source.url:
                                openai_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": block.source.url}
                                })
                            elif block.source.type == "base64" and block.source.data:
                                media_type = block.source.media_type or "image/jpeg"
                                openai_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{media_type};base64,{block.source.data}"}
                                })
                        elif block.type == "tool_use":
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "content": json.dumps(block.input) if isinstance(block.input, dict) else str(block.input)
                                }
                            })
                        elif block.type == "tool_result":
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": block.tool_use_id,
                                "content": block.content if isinstance(block.content, str) else json.dumps(block.content) if block.content else ""
                            })

                if openai_content:
                    if len(openai_content) == 1 and openai_content[0].get("type") == "text":
                        openai_msg["content"] = openai_content[0]["text"]
                    else:
                        openai_msg["content"] = openai_content

                if tool_calls:
                    openai_msg["tool_calls"] = tool_calls

                # Add tool results as separate messages
                for tr in tool_results:
                    messages.append(tr)

        messages.append(openai_msg)

    # Build OpenAI request params
    params: Dict[str, Any] = {
        "model": anthropic_request.model,
        "messages": messages,
        "max_tokens": anthropic_request.max_tokens,
    }

    # Map optional parameters
    if anthropic_request.temperature is not None:
        params["temperature"] = anthropic_request.temperature
    if anthropic_request.top_p is not None:
        params["top_p"] = anthropic_request.top_p
    if anthropic_request.stop_sequences:
        params["stop"] = anthropic_request.stop_sequences
    if anthropic_request.stream is not None:
        params["stream"] = anthropic_request.stream

    # Convert tools format
    if anthropic_request.tools:
        openai_tools = []
        for tool in anthropic_request.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema
                }
            })
        params["tools"] = openai_tools

    # Convert tool_choice
    if anthropic_request.tool_choice:
        tc = anthropic_request.tool_choice
        if tc.type == "auto":
            params["tool_choice"] = "auto"
        elif tc.type == "none":
            params["tool_choice"] = "none"
        elif tc.type == "any":
            params["tool_choice"] = "required"
        elif tc.type == "tool" and tc.name:
            params["tool_choice"] = {"type": "function", "function": {"name": tc.name}}

    return params


def convert_openai_to_anthropic_response(
    openai_response: Dict[str, Any],
    anthropic_model: str
) -> Dict[str, Any]:
    """Convert OpenAI Chat Completion response to Anthropic Messages format."""
    message_id = openai_response.get("id", f"msg_{uuid.uuid4().hex[:24]}")

    # Extract content
    content_blocks = []
    stop_reason = "end_turn"

    choices = openai_response.get("choices", [])
    if choices:
        choice = choices[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        # Map finish reasons
        if finish_reason == "length":
            stop_reason = "max_tokens"
        elif finish_reason == "stop":
            stop_reason = "end_turn"
        elif finish_reason == "tool_calls":
            stop_reason = "tool_use"

        # Add text content
        text_content = message.get("content")
        if text_content:
            content_blocks.append({"type": "text", "text": text_content})

        # Add tool calls
        tool_calls = message.get("tool_calls", [])
        for tc in tool_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                try:
                    tool_input = json.loads(func.get("content", "{}"))
                except (json.JSONDecodeError, TypeError):
                    tool_input = {"raw": func.get("content", "")}
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
                    "name": func.get("name", ""),
                    "input": tool_input
                })

    # Ensure at least one content block
    if not content_blocks:
        content_blocks.append({"type": "text", "text": ""})

    # Extract usage
    usage_data = openai_response.get("usage", {})
    anthropic_usage = {
        "input_tokens": usage_data.get("prompt_tokens", 0),
        "output_tokens": usage_data.get("completion_tokens", 0)
    }

    return {
        "id": message_id,
        "type": "message",
        "role": "assistant",
        "content": content_blocks,
        "model": anthropic_model,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": anthropic_usage
    }


def convert_openai_chunk_to_anthropic_events(
    chunk: Dict[str, Any],
    anthropic_model: str,
    is_first: bool = False
) -> List[Dict[str, Any]]:
    """Convert OpenAI streaming chunk to Anthropic streaming events."""
    events = []

    if is_first:
        # Send message_start event
        message_id = chunk.get("id", f"msg_{uuid.uuid4().hex[:24]}")
        events.append({
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": anthropic_model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
        })

    # Process choices
    choices = chunk.get("choices", [])
    for choice in choices:
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")

        # Handle content delta
        content = delta.get("content")
        if content:
            events.append({
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""}
            })
            events.append({
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": content}
            })
            events.append({
                "type": "content_block_stop",
                "index": 0
            })

        # Handle tool calls
        tool_calls = delta.get("tool_calls", [])
        for i, tc in enumerate(tool_calls):
            if tc.get("type") == "function":
                func = tc.get("function", {})
                tc_id = tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}")
                tc_name = func.get("name", "")
                tc_args = func.get("arguments", "{}")

                events.append({
                    "type": "content_block_start",
                    "index": i + 1,
                    "content_block": {
                        "type": "tool_use",
                        "id": tc_id,
                        "name": tc_name
                    }
                })
                events.append({
                    "type": "content_block_delta",
                    "index": i + 1,
                    "delta": {"type": "input_json_delta", "partial_json": tc_args}
                })
                events.append({
                    "type": "content_block_stop",
                    "index": i + 1
                })

        # Handle finish
        if finish_reason:
            stop_reason = "end_turn"
            if finish_reason == "length":
                stop_reason = "max_tokens"
            elif finish_reason == "tool_calls":
                stop_reason = "tool_use"

            events.append({
                "type": "message_delta",
                "delta": {
                    "stop_reason": stop_reason,
                    "stop_sequence": None
                },
                "usage": {"output_tokens": 0}
            })

    return events
