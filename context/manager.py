"""
This module manages the conversation context for the Kraken Code agent.

It tracks message history, handles system prompts, and provides utilities
for converting internal message representations into the dictionary format
required by LLM APIs.
"""

from dataclasses import field
from typing import Any
from utils.text import count_tokens
from prompts.system_prompt import get_system_prompt
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class MessageItem:
    """
    Represents a single message in the conversation history.

    Attributes:
        role: The role of the speaker (e.g., "user", "assistant", "system").
        content: The text content of the message.
        tool_call_id: The ID of the tool call.
        tool_calls: A list of tool calls.
        token_count: The number of tokens occupied by this message (optional).
    """
    role: str
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    token_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the MessageItem to a standardized dictionary format.

        This format is compatible with the OpenAI/OpenRouter API specifications.

        Returns:
            A dictionary containing the role and content of the message.
        """

        result: dict[str, Any] = {"role": self.role}

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        if self.content:
            result["content"] = self.content

        return result
    


class ContextManager:
    """
    Manages the state and history of a conversation.

    The ContextManager is responsible for maintaining the system prompt,
    storing user and assistant messages, and calculating token usage for 
    context window management.
    """
    def __init__(self):
        """Initializes the ContextManager with the system prompt and an empty message list."""
        self._system_prompt = get_system_prompt()
        self._messages: list[MessageItem] = []
        self._model = os.getenv("MODEL")

    def add_user_message(self, message: str) -> None:
        """
        Adds a new message from the user to the conversation history.

        Args:
            message: The textual content of the user's message.
        """
        item = MessageItem(
            role="user",
            content=message,
            token_count=count_tokens(message, self._model)
        )
        self._messages.append(item)

    def add_assistant_message(self, message: str) -> None:
        """
        Adds a new message from the assistant to the conversation history.

        Args:
            message: The textual content of the assistant's message.
        """
        item = MessageItem(
            role="assistant",
            content=message or "",
            token_count=count_tokens(message or "", self._model)
        )
        self._messages.append(item)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """
        Adds a tool result to the conversation history.

        Args:
            tool_call_id: The ID of the tool call.
            content: The content of the tool result.
        """
        item = MessageItem(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            token_count=count_tokens(content, self._model)
        )
        self._messages.append(item)

    def get_messages(self) -> list[dict[str, Any]]:
        """
        Retrieves the full conversation history in the expected API format.

        This includes the system prompt (if present) followed by all 
        user and assistant interactions.

        Returns:
            A list of message dictionaries.
        """
        messages = []

        if self._system_prompt:
            messages.append({
                "role": "system",
                "content": self._system_prompt,
            })

        for item in self._messages:
            # We converted the item which in a MessageItem to dictionary to bridge the internal metadata and external API requirements.
            messages.append(item.to_dict())

        return messages
