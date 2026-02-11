"""
This module defines the events used by the Agent to communicate its internal state.

These events provide granular feedback to the user interface, allowing for
a transparent "glass box" view of the agent's internal reasoning and actions.
"""

from __future__ import annotations
from client.response import TokenUsage
from typing import Any
from dataclasses import dataclass, field
from enum import StrEnum

# @dataclass
class AgentEventType(StrEnum):
    """
    Available types of events the Agent can emit.
    
    Categorized by lifecycle stages and streaming feedback.
    """
    # Agent Lifecycle
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # Text Streaming
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"


@dataclass
class AgentEvent:
    """
    A structured message emitted by the Agent.

    Attributes:
        type: The category of the event (START, END, DELTA, etc.).
        data: A dictionary containing event-specific information (e.g., content, error details).
    """
    type: AgentEventType
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent:
        """Creates an event signaling the start of an agent interaction."""
        return cls(
            type=AgentEventType.AGENT_START,
            data={"message": message},
        )

    @classmethod
    def agent_end(
        cls,
        response: str | None = None,
        usage: TokenUsage | None = None,
    ) -> AgentEvent:
        """Creates an event signaling the completion of an agent interaction."""
        return cls(
            type=AgentEventType.AGENT_END,
            data={
                "response": response, 
                "usage": usage.__dict__ if usage else None
            },
        )

    @classmethod
    def agent_error(
        cls,
        error: str,
        details: str | None = None
    ) -> AgentEvent:
        """Creates an event signaling that an error occurred."""
        return cls(
            type=AgentEventType.AGENT_ERROR,
            data={
                "error": error,
                "details": details or {},
            },
        )

    @classmethod
    def text_delta(cls, content: str) -> AgentEvent:
        """Creates an event containing a chunk of generated text."""
        return cls(
            type=AgentEventType.TEXT_DELTA,
            data={"content": content},
        )

    @classmethod
    def text_complete(cls, content: str) -> AgentEvent:
        """Creates an event containing the final completed text response."""
        return cls(
            type=AgentEventType.TEXT_COMPLETE,
            data={"content": content},
        )

    

    


# ------------------------------------------------------------
# The Trap: Setting data: dict = {} makes every instance of 
# AgentEvent share the exact same dictionary in memory.
# The Fix: default_factory=dict ensures Python creates a brand-new dictionary every time you instantiate the class.
# The Benefit: Total isolation. Changing the data in event_start won't accidentally overwrite the data in event_delta.
# Essentially, it's the difference between sharing a single notebook (the bug) and giving everyone their own fresh notebook (the fix).