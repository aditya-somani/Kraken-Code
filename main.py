from client.llm_client import LLMClient
import asyncio

async def main():
    llm_client = LLMClient()
    messages = [
        {"role": "user", "content": "Write me a joke about AI."}
    ]
    # response = await llm_client.chat_completion(messages, False)
    # print(response)
    async for event in llm_client.chat_completion(messages, True):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
