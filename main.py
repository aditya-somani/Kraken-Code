from client.llm_client import LLMClient
import asyncio

async def main():
    llm_client = LLMClient()
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    response = await llm_client.chat_completion(messages, False)
    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
