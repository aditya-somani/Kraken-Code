from __future__ import annotations
from client.response import TokenUsage
from typing import Any
from dataclasses import dataclass, field
from enum import StrEnum

# @dataclass
class AgentEventType(StrEnum):
    # Agent Lifecycle
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # Text Streaming
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"


@dataclass
class AgentEvent:
    type: AgentEventType
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent:
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
        return cls(
            type=AgentEventType.AGENT_ERROR,
            data={
                "error": error,
                "details": details or {},
            },
        )

    @classmethod
    def text_delta(cls, content: str) -> AgentEvent:
        return cls(
            type=AgentEventType.TEXT_DELTA,
            data={"content": content},
        )

    @classmethod
    def text_complete(cls, content: str) -> AgentEvent:
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