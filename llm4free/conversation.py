"""
conversation.py

This module provides a modern conversation manager for handling chat-based
interactions, message history, tool call tracking, and robust error handling.

Classes:
    Conversation: Main conversation manager class.
"""

import os
from typing import Any, Dict, List, Optional

from litprinter import ic


class Conversation:
    """Handles prompt generation based on history with optional tool call support.

    Supports both flat text history (legacy) and structured message history
    for tool/function calling workflows.
    """

    intro: str
    status: bool
    max_tokens_to_sample: int
    chat_history: str
    history_format: str
    file: Optional[str]
    update_file: bool
    history_offset: int
    prompt_allowance: int

    def __init__(
        self,
        status: bool = True,
        max_tokens: int = 600,
        filepath: Optional[str] = None,
        update_file: bool = True,
    ):
        """Initializes Conversation.

        Args:
            status: Flag to control history. Defaults to True.
            max_tokens: Maximum number of tokens to be generated upon completion.
            filepath: Path to file containing conversation history.
            update_file: Add new prompts and responses to the file.
        """
        self.intro = (
            "You're a Large Language Model for chatting with people. "
            "Assume role of the LLM and give your response."
        )
        self.status = status
        self.max_tokens_to_sample = max_tokens
        self.chat_history = ""
        self.history_format = "\nUser : %(user)s\nLLM :%(llm)s"
        self.file = filepath
        self.update_file = update_file
        self.history_offset = 10250
        self.prompt_allowance = 10
        self._messages: List[Dict[str, Any]] = []
        self.load_conversation(filepath, False) if filepath else None

    # ------------------------------------------------------------------ #
    #  Structured message API (for tool-calling workflows)
    # ------------------------------------------------------------------ #

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Return the structured message history."""
        return self._messages

    def add_message(self, role: str, content: str, **extra: Any) -> None:
        """Append a message to the structured history.

        Args:
            role: Message role (system / user / assistant / tool).
            content: Text content.
            **extra: Additional keys such as tool_calls or tool_call_id.
        """
        msg: Dict[str, Any] = {"role": role, "content": content}
        msg.update(extra)
        self._messages.append(msg)

    def add_tool_call_result(self, tool_name: str, arguments: Dict[str, Any], result: str) -> None:
        """Record a tool execution result in structured history.

        This adds two entries: an assistant message showing the tool call,
        and a tool message with the result.

        Args:
            tool_name: Name of the tool that was called.
            arguments: Arguments passed to the tool.
            result: The tool execution result.
        """
        self._messages.append(
            {
                "role": "assistant",
                "content": f"[Tool Call: {tool_name}({arguments})]",
            }
        )
        self._messages.append(
            {
                "role": "tool",
                "content": result,
                "tool_name": tool_name,
            }
        )

    def gen_messages_with_tools(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Build a full message list including the new user prompt.

        Useful for providers that accept an OpenAI-style messages array
        but still want tool-call history preserved.

        Args:
            prompt: The current user prompt.
            system_prompt: Optional system prompt override.

        Returns:
            List of message dicts ready to send to an API.
        """
        msgs: List[Dict[str, Any]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(self._messages)
        msgs.append({"role": "user", "content": prompt})
        return msgs

    # ------------------------------------------------------------------ #
    #  Legacy flat-text API (backward compatible)
    # ------------------------------------------------------------------ #

    def load_conversation(self, filepath: str, exists: bool = True) -> None:
        """Load conversation into chat's history from .txt file.

        Args:
            filepath: Path to .txt file.
            exists: Flag for file availability.
        """
        assert isinstance(filepath, str), (
            f"Filepath needs to be of str datatype not {type(filepath)}"
        )
        assert os.path.isfile(filepath) if exists else True, f"File '{filepath}' does not exist"
        if not os.path.isfile(filepath):
            ic(f"Creating new chat-history file - '{filepath}'")
            with open(filepath, "w") as fh:
                fh.write(self.intro)
        else:
            ic(f"Loading conversation from '{filepath}'")
            with open(filepath) as fh:
                file_contents = fh.readlines()
                if file_contents:
                    self.intro = file_contents[0]
                    self.chat_history = "\n".join(file_contents[1:])

    def __trim_chat_history(self, chat_history: str, intro: str) -> str:
        """Ensures the len(prompt) and max_tokens_to_sample is not > 4096."""
        len_of_intro = len(intro)
        len_of_chat_history = len(chat_history)
        total = self.max_tokens_to_sample + len_of_intro + len_of_chat_history
        if total > self.history_offset:
            truncate_at = (total - self.history_offset) + self.prompt_allowance
            trimmed_chat_history = chat_history[truncate_at:]
            return "... " + trimmed_chat_history
        return chat_history

    def gen_complete_prompt(
        self,
        prompt: str,
        intro: Optional[str] = None,
        tool_definitions: Optional[str] = None,
    ) -> str:
        """Generates a complete prompt with history and optional tool definitions.

        Args:
            prompt: Chat prompt.
            intro: Override class intro.
            tool_definitions: Formatted tool definitions to inject before history.

        Returns:
            Updated incomplete chat_history string.
        """
        if self.status:
            intro = self.intro if intro is None else intro
            incomplete_chat_history = self.chat_history + self.history_format % dict(
                user=prompt, llm=""
            )
            full = intro + self.__trim_chat_history(incomplete_chat_history, intro)
            if tool_definitions:
                full = tool_definitions + "\n\n" + full
            return full

        if tool_definitions:
            return tool_definitions + "\n\n" + prompt
        return prompt

    def update_chat_history(self, prompt: str, response: str, force: bool = False) -> None:
        """Updates chat history.

        Args:
            prompt: user prompt.
            response: LLM response.
            force: Force update even when status is False.
        """
        if not self.status and not force:
            return
        new_history = self.history_format % dict(user=prompt, llm=response)
        if self.file and self.update_file:
            if os.path.exists(self.file):
                with open(self.file, "a") as fh:
                    fh.write(new_history)
            else:
                with open(self.file, "w") as fh:
                    fh.write(self.intro + "\n" + new_history)
        self.chat_history += new_history

        # Also track in structured messages
        self._messages.append({"role": "user", "content": prompt})
        self._messages.append({"role": "assistant", "content": response})
