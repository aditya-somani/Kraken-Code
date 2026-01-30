
# Agent Class: The blueprint (the "brain") that maintains the state of a conversation, handles API calls, 
# and decides which tools to trigger based on the user's request.
# This is the middle layer between the user and the LLM. It will manage everything.
from typing import AsyncGenerator
class Agent:
    def __init__(self):
        pass
    
    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        

# ---------------------------------------------------------------------------------------------------------------
# WHY AGENTEVENT?
# Standard stream events are too "coarse-grained" for an autonomous agent. 
# They only track text generation, leaving the user blind during internal cycles.
#
# By using a microscopic 'AgentEvent' structure via an AsyncGenerator, we can:
# 1. Provide a "Heartbeat": Show the user the agent is active during context pruning.
# 2. Tool Transparency: Stream tool calls and arguments before they execute.
# 3. State Awareness: Surface background tasks (like memory management) in real-time.
#
# This ensures the 'Agentic Loop' is a glass box, not a black box, for the user.