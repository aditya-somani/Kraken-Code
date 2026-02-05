import sys
from UI.TUI import get_console, TUI
from client.llm_client import LLMClient
from typing import Any
from agent.event import AgentEventType
import asyncio
from agent.agent import Agent
import click
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
    def __init__(self):
        self.agent : Agent | None = None
        self.tui = TUI(console=console)

    async def run_single(self, message: str) -> str | None:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None

        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                self.tui.stream_assistant_messages(content)

            # if event.type == AgentEventType.TEXT_COMPLETE:
            #     self.tui.stream_assistant_messages(event.data.get("content", ""))
            
            if event.type == AgentEventType.AGENT_ERROR:
                self.tui.stream_assistant_messages(event.data.get("error", ""))

# wrapper function to pause and wait for the final result
# async def run(
#     messages: list[dict[str, Any]],
# ):


@click.command()
@click.argument("prompt", required=False) # We don't want to always pass a prompt; sometimes we just want to run without a prompt.
def main(
    prompt: str | None = None
):
    cli = CLI()
    # messages = [
    #     {"role": "user", "content": prompt}
    # ]
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)

if __name__ == "__main__":
    main()