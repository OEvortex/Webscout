"""
conversation.py

This module provides a modern conversation manager for handling chat-based interactions, message history, and robust error handling. It defines the Conversation class for managing conversational state.

Classes:
    Conversation: Main conversation manager class.
"""
import os
from typing import Optional

from litprinter import ic


class Conversation:
    """Handles prompt generation based on history"""
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
        """Initializes Conversation

        Args:
            status (bool, optional): Flag to control history. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
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
        self.load_conversation(filepath, False) if filepath else None

    def load_conversation(self, filepath: str, exists: bool = True) -> None:
        """Load conversation into chat's history from .txt file

        Args:
            filepath (str): Path to .txt file
            exists (bool, optional): Flag for file availability. Defaults to True.
        """
        assert isinstance(
            filepath, str
        ), f"Filepath needs to be of str datatype not {type(filepath)}"
        assert (
            os.path.isfile(filepath) if exists else True
        ), f"File '{filepath}' does not exist"
        if not os.path.isfile(filepath):
            ic(f"Creating new chat-history file - '{filepath}'")
            with open(filepath, "w") as fh:  # Try creating new file
                # lets add intro here
                fh.write(self.intro)
        else:
            ic(f"Loading conversation from '{filepath}'")
            with open(filepath) as fh:
                file_contents = fh.readlines()
                if file_contents:
                    self.intro = file_contents[0]  # Presume first line is the intro.
                    self.chat_history = "\n".join(file_contents[1:])

    def __trim_chat_history(self, chat_history: str, intro: str) -> str:
        """Ensures the len(prompt) and max_tokens_to_sample is not > 4096"""
        len_of_intro = len(intro)
        len_of_chat_history = len(chat_history)
        total = (
            self.max_tokens_to_sample + len_of_intro + len_of_chat_history
        )  # + self.max_tokens_to_sample
        if total > self.history_offset:
            truncate_at = (total - self.history_offset) + self.prompt_allowance
            # Remove head of total (n) of chat_history
            trimmed_chat_history = chat_history[truncate_at:]
            return "... " + trimmed_chat_history
            # print(len(self.chat_history))
        else:
            return chat_history

    def gen_complete_prompt(self, prompt: str, intro: Optional[str] = None) -> str:
        """Generates a kinda like incomplete conversation

        Args:
            prompt (str): Chat prompt
            intro (str): Override class' intro. Defaults to None.

        Returns:
            str: Updated incomplete chat_history
        """
        if self.status:
            intro = self.intro if intro is None else intro
            incomplete_chat_history = self.chat_history + self.history_format % dict(
                user=prompt, llm=""
            )
            return intro + self.__trim_chat_history(incomplete_chat_history, intro)

        return prompt

    def update_chat_history(
        self, prompt: str, response: str, force: bool = False
    ) -> None:
        """Updates chat history

        Args:
            prompt (str): user prompt
            response (str): LLM response
            force (bool, optional): Force update
        """
        if not self.status and not force:
            return
        new_history = self.history_format % dict(user=prompt, llm=response)
        if self.file and self.update_file:
            if os.path.exists(self.file):
                # Append new history to existing file
                with open(self.file, "a") as fh:
                    fh.write(new_history)
            else:
                # Create new file with intro and new history
                with open(self.file, "w") as fh:
                    fh.write(self.intro + "\n" + new_history)
        self.chat_history += new_history

