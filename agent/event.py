from typing import Any
from dataclasses import dataclass, field
from enum import StrEnum

@dataclass
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


# ------------------------------------------------------------
# The Trap: Setting data: dict = {} makes every instance of 
# AgentEvent share the exact same dictionary in memory.
# The Fix: default_factory=dict ensures Python creates a brand-new dictionary every time you instantiate the class.
# The Benefit: Total isolation. Changing the data in event_start won't accidentally overwrite the data in event_delta.
# Essentially, it's the difference between sharing a single notebook (the bug) and giving everyone their own fresh notebook (the fix).