"""
This module contains the core Agent logic for Kraken Code.

The Agent acts as the orchestrator, managing high-level conversation flow,
context, and interactions with the LLM client.
"""

from __future__ import annotations
from typing import AsyncGenerator
from agent.event import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.response import StreamEventType
from context.manager import ContextManager

class Agent:
    """
    The central intelligence unit of the application.
    
    The Agent maintains the state of a conversation, handles API calls to the LLM,
    and coordinates between the user interface and the underlying language model.
    It acts as the middle layer that manages context and tools.
    """
    def __init__(self):
        """Initializes the Agent with a new LLM client and context manager."""
        self.llm_client = LLMClient()
        self.context_manager = ContextManager()

    async def run(self, message: str) -> AsyncGenerator[AgentEvent, None]:
        """
        Starts an interaction cycle with a user message.

        This method handles the high-level flow: starting the session,
        updating context, running the agentic loop, and ending the session.

        Args:
            message: The user's input string.

        Yields:
            AgentEvent: Granular events representing the agent's progress and output.
        """
        self._current_message = message
        yield AgentEvent.agent_start(message)
        
        # add user message to context
        self.context_manager.add_user_message(message)

        final_response: str | None = None

        async for event in self._agentic_loop():
            yield event
            
            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content", "")

        yield AgentEvent.agent_end(final_response)
    
    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        """
        The internal loop where the Agent communicates with the LLM.

        This method handles streaming responses from the LLM client,
        yields text deltas, and handles potential errors during the process.
        It also updates the context manager with the assistant's final response.

        Yields:
            AgentEvent: Text deltas, completion events, or error events.
        """
        # messages = [
        #     {"role": "user", "content": "Hello"}
        # ] -> This is the structure the LLM API expects. 
        messages = self.context_manager.get_messages()
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

        self.context_manager.add_assistant_message(
            response_text or None,
        )
        if response_text:
            yield AgentEvent.text_complete(response_text)

    async def __aenter__(self) -> Agent:
        """Asynchronous context manager entry."""
        return self
    
    async def __aexit__(
        self,
        exc_type,
        exc_val,
        exc_tb
    ) -> None:
        """
        Asynchronous context manager exit.
        
        Ensures that resources like the LLM client are properly closed.
        """
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
