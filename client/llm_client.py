from email import message
from typing import Any
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# https://openrouter.ai/docs/quickstart#using-the-openai-sdk -> OpenRouter Docs
# https://github.com/openai/openai-python?tab=readme-ov-file#async-usage -> OpenAI Python SDK Docs


class LLMClient:
    def __init__(self) -> None:
        self._client : AsyncOpenAI | None = None

    # We are not coupling the model when we are creating the client. So that afterwards, We can choose different models for different messages instead of having a same model.
    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
                base_url=os.getenv("OPENROUTER_BASE_URL", ""),
            )
        return self._client            

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True,
    ):
        client = self.get_client()
        kwargs = {
            "model": "mistralai/devstral-2512:free", # Free model - Hard coding for now...
            "messages": messages,
            "stream": stream,
        }
        
        if stream:
            return await self._stream_response()
        else:
            return await self._non_stream_response(client, kwargs)

    async def _stream_response(self):
        pass

    async def _non_stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ):
        response = await client.chat.completions.create(**kwargs)
        choices = response.choices[0]
        message = choices.message
        content = None
        
        if message:
            content = message.content

    """
ChatCompletion(id='gen-1768299571-4Fh72rFHC1w2z1OOmMix', 
choices=[Choice(finish_reason='stop', index=0, logprobs=None, 
message=ChatCompletionMessage(content="Hello! �  I'm just a virtual assistant, so I don't have feelings, 
but I'm here and ready to help you with anything you need! How about you—how are you doing today? 
Anything on your mind or something I can assist with?", 
refusal=None, role='assistant', 
annotations=None, audio=None help you with anything you need! How about you—how are you doing today? 
Anything on your mind or something I can assist with?", 
refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, reasoning=None), 
native_finish_reason='stop')], created=1768299572, model='mistralai/devstral-2512:free', object='chat.completion', 
service_tier=None, system_fingerprint=None, usage=CompletionUsage(completion_tokens=55, prompt_tokens=9, total_tokens=64, 
completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=None, audio_tokens=None, reasoning_tokens=0, 
rejected_prediction_tokens=None), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0), cost=0, 
is_byok=False, cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 
'upstream_inference_completions_cost': 0}), provider='Mistral')
    """
