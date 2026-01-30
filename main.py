from client.llm_client import LLMClient
from typing import Any
import asyncio
import click
# Click natively does not support asynchronous functions.
# We use this wrapper (middleman/middle function) to pause and wait for the final result, 
# ensuring Click receives the actual output rather than a raw coroutine object.

# How do I know that? Because I ran this program with async def main(), it gave me this as output.
# H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
# $ python main.py "Hey"
# sys:1: RuntimeWarning: coroutine 'main' was never awaited
# RuntimeWarning: Enable tracemalloc to get the object allocation traceback

class CLI:
    def __init__(self):
        pass

    def run_single(self):
        pass

# wrapper function to pause and wait for the final result
async def run(
    messages: list[dict[str, Any]],
):
    llm_client = LLMClient()
    async for event in llm_client.chat_completion(messages, False):
        print(event)

@click.command()
@click.argument("prompt", required=False) # We don't want to always pass a prompt; sometimes we just want to run without a prompt.
def main(
    prompt: str | None = None
):
    print(f"Prompt: {prompt}")
    messages = [
        {"role": "user", "content": prompt}
    ]
    asyncio.run(run(messages))
    print("Done")

if __name__ == "__main__":
    main()