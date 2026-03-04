"""
This is the entry point for the Kraken Code CLI application.

It provides a command-line interface for interacting with the Kraken Code Agent,
handling user input, streaming assistant responses, and managing the application lifecycle.
"""

# Standard Library Imports
import sys
import os
import asyncio
from pathlib import Path
from typing import Any

# Third-Party Imports
import click
import dotenv

# Local Application Imports
from UI.TUI import get_console, TUI
from client.llm_client import LLMClient
from agent.event import AgentEventType
from agent.agent import Agent

# Load environment variables
dotenv.load_dotenv()

# Click natively does not support asynchronous functions.
# We use this wrapper (middleman/middle function) to pause and wait for the final result, 
# ensuring Click receives the actual output rather than a raw coroutine object.

# How do I know that? Because I ran this program with async def main(), it gave me this as output.
# H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
# $ python main.py "Hey"
# sys:1: RuntimeWarning: coroutine 'main' was never awaited
# RuntimeWarning: Enable tracemalloc to get the object allocation traceback

console = get_console()

class CLI:
    """
    Manages the Command Line Interface interaction logic.
    
    The CLI class bridges the gap between the user's terminal and the Agent's
    internal logic, handling event streaming and display.
    """
    def __init__(self):
        """Initializes the CLI with an Agent (initially None) and a TUI instance."""
        self.agent : Agent | None = None
        self.tui = TUI(console=console)

    async def run_single(self, message: str) -> str | None:
        """
        Runs a single interaction cycle with the Agent.

        Args:
            message: The user's input prompt.

        Returns:
            The final textual response from the assistant, or None if failed.
        """
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def run_interactive(self) -> str | None:
        """
        Runs an interactive loop with the Agent.

        This method allows the user to continuously interact with the Agent
        by entering prompts and receiving responses until the user decides to exit.

        Returns:
            The final textual response from the assistant, or None if failed.
        """
        self.tui.print_welcome(
            title="Kraken Code",
            lines=[
                f"Model: {os.getenv('MODEL')}",
                f"CWD: {Path.cwd()}",
                "Commands: /help /config /approval /model /exit"
            ]
        )

        async with Agent() as agent:
            self.agent = agent
            
            while True:
                try:
                    user_input = console.input("[cyan bold]❯ [/cyan bold]").strip()
                    if not user_input:
                        continue

                    await self._process_message(user_input)

                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit[\dim]")
                except EOFError:
                    break

        console.print("\n[dim]Exiting Kraken Code...[/dim]")

    def _get_tool_kind(self, tool_name: str) -> str | None:
        """
        Gets the kind of a tool by its name.

        Args:
            tool_name: The name of the tool.

        Returns:
            The kind of the tool, or None if the tool is not found.
        """
        tool = self.agent.tool_registry.get(tool_name)
        if not tool:
            return None
        else:
            return tool.kind.value

    async def _process_message(self, message: str) -> str | None:
        """
        Processes a message by streaming events from the Agent.

        Internal method that iterates over AgentEvents, updating the TUI
        in real-time as text is generated or errors occur.

        Args:
            message: The user's input prompt.

        Returns:
            The final completed response string.
        """
        if not self.agent:
            return None

        assistant_streaming = False
        final_response: str | None = None

        async for event in self.agent.run(message):
            # print(event)
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                if not assistant_streaming:
                    self.tui.begin_assitant()
                    assistant_streaming = True
                self.tui.stream_assistant_messages(content)

            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content", "")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False
            
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error", "Unknown error occured.")
                console.print(f'[error]Error: {error}[/error]')

            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "Unknown tool")
                self.tui.tool_call_start(
                    call_id=event.data.get("call_id", ""),
                    name=tool_name,
                    tool_kind=self._get_tool_kind(tool_name),
                    arguments=event.data.get("arguments", {}),
                )

            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get("name", "Unknown tool")
                self.tui.tool_call_complete(
                    call_id=event.data.get("call_id", ""),
                    name=tool_name,
                    tool_kind=self._get_tool_kind(tool_name),
                    success=event.data.get("success", False),
                    output=event.data.get("output", ""),
                    error=event.data.get("error", None),
                    metadata=event.data.get("metadata", None),
                    truncated=event.data.get("truncated", False),
                )

        return final_response

# wrapper function to pause and wait for the final result
# async def run(
#     messages: list[dict[str, Any]],
# ):


@click.command()
@click.argument("prompt", required=False) # We don't want to always pass a prompt; sometimes we just want to run without a prompt.
def main(
    prompt: str | None = None
):
    """
    Main entry point for the Kraken Code CLI.
    
    Args:
        prompt: An optional initial user prompt to process.
    """
    cli = CLI()
    # messages = [
    #     {"role": "user", "content": prompt}
    # ]
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
    else:
        asyncio.run(cli.run_interactive())

if __name__ == "__main__":
    main()