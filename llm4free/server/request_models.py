"""
Pydantic models for API requests and responses.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import ConfigDict

try:
    from llm4free.llm.pydantic_imports import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


# Define Pydantic models for multimodal content parts, aligning with OpenAI's API
class TextPart(BaseModel):
    """Text content part for multimodal messages."""

    type: Literal["text"]
    text: str


class ImageURL(BaseModel):
    """Image URL configuration for multimodal messages."""

    url: str  # Can be http(s) or data URI
    detail: Optional[Literal["auto", "low", "high"]] = Field(
        "auto", description="Specifies the detail level of the image."
    )


class ImagePart(BaseModel):
    """Image content part for multimodal messages."""

    type: Literal["image_url"]
    image_url: ImageURL


MessageContentParts = Union[TextPart, ImagePart]


class Message(BaseModel):
    """Chat message model compatible with OpenAI API."""

    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Optional[Union[str, List[MessageContentParts]]] = Field(
        None,
        description="The content of the message. Can be a string, a list of content parts (for multimodal), or null.",
    )
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Tool calls that the assistant should make, used in assistant messages when tool use is enabled.",
    )
    tool_call_id: Optional[str] = Field(
        None,
        description="Tool call ID for tool messages, used to match tool calls with tool responses.",
    )


# Tool calling models
class FunctionParameters(BaseModel):
    """Parameters for a function tool."""

    type: Literal["object"] = "object"
    properties: Optional[Dict[str, Any]] = Field(
        None, description="The parameters the function accepts."
    )
    required: Optional[List[str]] = Field(None, description="List of required parameter names.")
    additionalProperties: Optional[bool] = Field(
        None, description="Whether additional properties are allowed."
    )


class FunctionDefinition(BaseModel):
    """Definition of a function tool (deprecated in favor of tools, but kept for compatibility)."""

    name: str = Field(..., description="The name of the function to call.")
    description: Optional[str] = Field(None, description="A description of what the function does.")
    parameters: FunctionParameters = Field(..., description="The parameters the function accepts.")
    strict: Optional[bool] = Field(
        None, description="Whether the function parameters must strictly match the schema."
    )


class ToolFunction(BaseModel):
    """Function tool definition for tools array."""

    type: Literal["function"] = "function"
    function: FunctionDefinition = Field(..., description="The function definition.")


# Union type for all tool types
ToolUnion = Union[ToolFunction, Dict[str, Any]]


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions."""

    model: str = Field(
        ..., description="ID of the model to use. See the model endpoint for the available models."
    )
    messages: List[Message] = Field(
        ..., description="A list of messages comprising the conversation so far."
    )
    temperature: Optional[float] = Field(
        None, description="What sampling temperature to use, between 0 and 2."
    )
    top_p: Optional[float] = Field(
        None, description="An alternative to sampling with temperature, called nucleus sampling."
    )
    n: Optional[int] = Field(
        1, description="How many chat completion choices to generate for each input message."
    )
    stream: Optional[bool] = Field(
        False, description="If set, partial message deltas will be sent, like in ChatGPT."
    )
    max_tokens: Optional[int] = Field(
        None, description="The maximum number of tokens to generate in the chat completion."
    )
    presence_penalty: Optional[float] = Field(
        None,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far.",
    )
    frequency_penalty: Optional[float] = Field(
        None,
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far.",
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        None, description="Modify the likelihood of specified tokens appearing in the completion."
    )
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user.")
    stop: Optional[Union[str, List[str]]] = Field(
        None, description="Up to 4 sequences where the API will stop generating further tokens."
    )

    # Tool calling support
    tools: Optional[List[ToolUnion]] = Field(
        None,
        description="A list of tools the model may call. Currently only function tools are supported.",
    )
    tool_choice: Optional[Union[Literal["none", "auto", "required"], Dict[str, Any]]] = Field(
        None,
        description="Controls which (if any) tool is called by the model. 'none' means no tool calling, 'auto' means the model can choose, 'required' means the model must call a tool. Can also be a dict specifying a particular tool.",
    )
    parallel_tool_calls: Optional[bool] = Field(
        None, description="Whether to enable parallel tool calling during tool use."
    )

    # Deprecated fields (kept for backward compatibility)
    functions: Optional[List[FunctionDefinition]] = Field(
        None,
        description="DEPRECATED: Use 'tools' instead. A list of functions the model may generate JSON inputs for.",
    )
    function_call: Optional[Union[Literal["none", "auto"], Dict[str, str]]] = Field(
        None,
        description="DEPRECATED: Use 'tool_choice' instead. Controls which (if any) function is called by the model.",
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "model": "Cloudflare/@cf/meta/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"},
                ],
                "temperature": 0.7,
                "max_tokens": 150,
                "stream": False,
            }
        },
    )


class ImageGenerationRequest(BaseModel):
    """Request model for OpenAI-compatible image generation endpoint."""

    prompt: str = Field(
        ...,
        description="A text description of the desired image(s). The maximum length is 1000 characters.",
    )
    model: str = Field(..., description="The model to use for image generation.")
    n: Optional[int] = Field(
        1, description="The number of images to generate. Must be between 1 and 10."
    )
    size: Optional[str] = Field(
        "1024x1024",
        description="The size of the generated images. Must be one of: '256x256', '512x512', or '1024x1024'.",
    )
    response_format: Optional[Literal["url", "b64_json"]] = Field(
        "url", description="The format in which the generated images are returned."
    )
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user.")
    style: Optional[str] = Field(
        None, description="Optional style for the image (provider/model-specific)."
    )
    aspect_ratio: Optional[str] = Field(
        None, description="Optional aspect ratio for the image (provider/model-specific)."
    )
    timeout: Optional[int] = Field(
        None, description="Optional timeout for the image generation request in seconds."
    )
    image_format: Optional[str] = Field(
        None, description="Optional image format (e.g., 'png', 'jpeg')."
    )
    seed: Optional[int] = Field(None, description="Optional random seed for reproducibility.")

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "prompt": "A futuristic cityscape at sunset, digital art",
                "model": "PollinationsAI/turbo",
                "n": 1,
                "size": "1024x1024",
                "response_format": "url",
                "user": "user-1234",
            }
        },
    )


class SpeechGenerationRequest(BaseModel):
    """Request model for OpenAI-compatible speech generation endpoint."""

    input: str = Field(
        ..., description="The text to generate audio for. The maximum length is 4096 characters."
    )
    model: str = Field(..., description="The model to use for speech generation.")
    voice: Optional[str] = Field("alloy", description="The voice to use when generating the audio.")
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = Field(
        "mp3",
        description="The format to audio in. Supported formats are mp3, opus, aac, flac, wav, and pcm.",
    )
    speed: Optional[float] = Field(
        1.0, description="The speed of the generated audio. Select a value from 0.25 to 4.0."
    )
    instructions: Optional[str] = Field(
        None, description="Voice instructions for controlling speech aspects."
    )
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user.")
    stream: Optional[bool] = Field(False, description="If set, the audio will be streamed.")

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "input": "Hello, welcome to LLM4Free AI!",
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "response_format": "mp3",
                "speed": 1.0,
            }
        },
    )


class ModelInfo(BaseModel):
    """Model information for the models endpoint."""

    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelListResponse(BaseModel):
    """Response model for the models list endpoint."""

    object: str = "list"
    data: List[ModelInfo]


class ErrorDetail(BaseModel):
    """Error detail structure compatible with OpenAI API."""

    message: str
    type: str = "server_error"
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response structure compatible with OpenAI API."""

    error: ErrorDetail


# ============================================================================
# Anthropic API Models
# ============================================================================


class AnthropicTextBlock(BaseModel):
    """Text content block for Anthropic messages."""

    type: Literal["text"] = "text"
    text: str


class AnthropicImageSource(BaseModel):
    """Image source for Anthropic messages."""

    type: Literal["base64", "url"] = "base64"
    media_type: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None


class AnthropicImageBlock(BaseModel):
    """Image content block for Anthropic messages."""

    type: Literal["image"] = "image"
    source: AnthropicImageSource


class AnthropicToolUseBlock(BaseModel):
    """Tool use content block for Anthropic messages."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class AnthropicToolResultBlock(BaseModel):
    """Tool result content block for Anthropic messages."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: Optional[Union[str, List[Dict[str, Any]]]] = None
    is_error: Optional[bool] = None


AnthropicContentBlock = Union[
    AnthropicTextBlock, AnthropicImageBlock, AnthropicToolUseBlock, AnthropicToolResultBlock
]


class AnthropicMessage(BaseModel):
    """Message model for Anthropic API."""

    role: Literal["user", "assistant"]
    content: Union[str, List[AnthropicContentBlock]]


class AnthropicToolDefinition(BaseModel):
    """Tool definition for Anthropic API."""

    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]


class AnthropicToolChoice(BaseModel):
    """Tool choice configuration for Anthropic API."""

    type: Literal["auto", "any", "tool", "none"] = "auto"
    name: Optional[str] = None
    disable_parallel_tool_use: Optional[bool] = None


class AnthropicMessagesRequest(BaseModel):
    """Request model for Anthropic Messages API."""

    model: str = Field(..., description="The model that will complete your prompt.")
    messages: List[AnthropicMessage] = Field(..., description="Input messages.")
    max_tokens: int = Field(..., description="The maximum number of tokens to generate.")
    system: Optional[Union[str, List[AnthropicTextBlock]]] = Field(
        None, description="System prompt. Can be a string or array of text blocks."
    )
    temperature: Optional[float] = Field(None, description="Amount of randomness (0.0 to 1.0).")
    top_p: Optional[float] = Field(None, description="Nucleus sampling parameter.")
    top_k: Optional[int] = Field(None, description="Top-k sampling parameter.")
    stop_sequences: Optional[List[str]] = Field(None, description="Custom stop sequences.")
    stream: Optional[bool] = Field(False, description="Whether to stream the response.")
    tools: Optional[List[AnthropicToolDefinition]] = Field(
        None, description="Tools the model may use."
    )
    tool_choice: Optional[AnthropicToolChoice] = Field(
        None, description="How the model should use tools."
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the request.")

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello, Claude"}],
            }
        },
    )


class AnthropicTextResponseBlock(BaseModel):
    """Text content block in Anthropic response."""

    type: Literal["text"] = "text"
    text: str


class AnthropicToolUseResponseBlock(BaseModel):
    """Tool use content block in Anthropic response."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class AnthropicUsage(BaseModel):
    """Usage information for Anthropic response."""

    input_tokens: int
    output_tokens: int


class AnthropicMessagesResponse(BaseModel):
    """Response model for Anthropic Messages API."""

    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[Union[AnthropicTextResponseBlock, AnthropicToolUseResponseBlock]]
    model: str
    stop_reason: Optional[Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]] = None
    stop_sequence: Optional[str] = None
    usage: AnthropicUsage
