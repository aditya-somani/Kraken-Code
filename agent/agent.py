from __future__ import annotations
from typing import AsyncGenerator
from agent.event import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.response import StreamEventType


# Agent Class: The blueprint (the "brain") that maintains the state of a conversation, handles API calls, 
# and decides which tools to trigger based on the user's request.
# This is the middle layer between the user and the LLM. It will manage everything.
class Agent:
    def __init__(self):
        self.llm_client = LLMClient()

    async def run(self, message: str):
        self._current_message = message
        yield AgentEvent.agent_start(message)
        # add user message to context

        final_response=""

        async for event in self._agentic_loop():
            yield event
            
            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content", "")

        yield AgentEvent.agent_end(final_response)
    
    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        # messages = [
        #     {"role": "user", "content": "Hello"}
        # ]
        messages = [
            {"role": "user", "content": self._current_message}
        ]
        response_text = ""
        async for event in self.llm_client.chat_completion(messages, True):
            if event.type == StreamEventType.TEXT_DELTA:
                if event.text_delta:
                    content = event.text_delta.content
                    if content:
                        yield AgentEvent.text_delta(content)
                        response_text += content
            elif event.type == StreamEventType.ERROR:
                yield AgentEvent.agent_error(event.error or "Unknow error occured.")

        if response_text:
            yield AgentEvent.text_complete(response_text)

    async def __aenter__(self) -> Agent:
        return self
    
    async def __aexit__(
        self,
        exc_type,
        exc_val,
        exc_tb
    ) -> None:
        if self.llm_client:
            await self.llm_client.close()
            self.llm_client = None
            
        

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