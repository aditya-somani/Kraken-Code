"""
This module provides the LLMClient for interacting with Large Language Models.

It wraps the AsyncOpenAI client to provide a consistent interface for both
streaming and non-streaming chat completions, with built-in retry logic
and error handling.
"""

from typing import Any, AsyncGenerator
from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
import os
from dotenv import load_dotenv
import asyncio

from client.response import StreamEvent, TextDelta, TokenUsage

load_dotenv()

# https://openrouter.ai/docs/quickstart#using-the-openai-sdk -> OpenRouter Docs
# https://github.com/openai/openai-python?tab=readme-ov-file#async-usage -> OpenAI Python SDK Docs


class LLMClient:
    """
    A client for managing communications with an LLM provider.
    
    Handles initialization, connection management, and execution of chat completion 
    requests with robust error handling and retry mechanisms.
    """
    def __init__(self) -> None:
        """Initializes the LLMClient with environment-based configuration."""
        self._client : AsyncOpenAI | None = None
        self._max_retries : int = int(os.getenv("MAX_RETRIES", 3))
        self._model : str = os.getenv("MODEL", "")

    def get_client(self) -> AsyncOpenAI:
        """
        Lazily initializes and returns the AsyncOpenAI client.

        This ensures the client is only created when needed, using the 
        OpenRouter API key and base URL from environment variables.

        Returns:
            The initialized AsyncOpenAI client.
        """
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
                base_url=os.getenv("OPENROUTER_BASE_URL", ""),
            )
        return self._client            

    async def close(self) -> None:
        """Closes the underlying HTTP client and resets the client state."""
        if self._client:
            await self._client.close()
            self._client = None

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Sends a chat completion request and yields the result as events.

        This is the primary method for interacting with the LLM. It supports
        both streaming and non-streaming modes and implements exponential backoff
        for transient errors like rate limits and connection issues.

        Args:
            messages: A list of message dictionaries (OpenAI format).
            stream: Whether to stream the response or wait for completion.

        Yields:
            StreamEvent: Events representing text deltas, completion, or errors.
        """

        client = self.get_client()
        kwargs = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
        }
        
        for attempt in range(self._max_retries + 1):
            try:
                if stream:
                    # Streaming case
                    async for event in self._stream_response(client, kwargs):
                        yield event
                else:
                    # Non-streaming case
                    event = await self._non_stream_response(client, kwargs)
                    yield event
                    # Why use yield in non-streaming case?
                    # Because of Architectural Uniformity (keeping things consistent).
                return
            except RateLimitError as e:
                #  If we encounter a rate limit error, we will retry the request.
                # This will be based on exponential backoff i.e. we will wait for a longer time before, each time before retrying the request.
                # ex: On first retry, we will wait for 1 second, on second retry, we will wait for 2 seconds, on third retry, we will wait for 4 seconds, and so on.
                if attempt < self._max_retries:
                    delay = 2 ** attempt # 2 ^ attempt
                    await asyncio.sleep(delay)
                else:
                    yield StreamEvent.stream_error(error=f"Rate limit error: {e}")
                    return

            except APIConnectionError as e:
                if attempt < self._max_retries:
                    delay = 2 ** attempt # 2 ^ attempt
                    await asyncio.sleep(delay)
                else:
                    yield StreamEvent.stream_error(error=f"API connection error: {e}")
                    return

            except APIError as e:
                # It acts as an umbrella for anything that goes wrong on the provider's side or during the transit of data.
                # No retries for this, just show error and return. It is a permanent error. Not a transient error like rate limit or connection error.
                yield StreamEvent.stream_error(error=f"API error: {e}")
                return

    async def _stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]: 
        """
        Internal method to handle the complexities of streaming responses.

        Processes chunks as they arrive, extracts text deltas, and handles
        final usage stats and termination reasons.

        Args:
            client: The AsyncOpenAI client.
            kwargs: Arguments for the completion call.

        Yields:
            StreamEvent: Text deltas and final completion event.
        """

        # There will be only one finish reason and one usage for the entire response.
        finish_reason : str | None = None
        usage : TokenUsage | None = None

        response = await client.chat.completions.create(**kwargs)
        # Iterating over the chunks of the response.
        async for chunk in response:
            # If the chunk has usage(last chunk), then we create a TokenUsage object.
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    completion_tokens=chunk.usage.completion_tokens,
                    prompt_tokens=chunk.usage.prompt_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=chunk.usage.prompt_tokens_details.cached_tokens,
                )

            # If there are no choices, then we skip the chunk.
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta.content:
                yield StreamEvent.stream_text(content=delta.content)

        yield StreamEvent.stream_message_complete(
            finish_reason=finish_reason, 
            usage=usage
        )
    
    async def _non_stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ) -> StreamEvent:
        """
        Internal method to handle non-streaming responses.

        Collects the entire response at once and packages it into a 
        consistent StreamEvent structure.

        Args:
            client: The AsyncOpenAI client.
            kwargs: Arguments for the completion call.

        Returns:
            A StreamEvent containing the complete response and usage stats.
        """
        response = await client.chat.completions.create(**kwargs)
        choices = response.choices[0]
        
        finish_reason = None
        if choices.finish_reason:
            finish_reason = choices.finish_reason
            
        message = choices.message
        
        text_delta = None
        if message.content:
            text_delta = TextDelta(message.content)

        usage = None
        if response.usage:
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.usage.prompt_tokens_details.cached_tokens,
            )

        return StreamEvent.stream_message_complete(
            finish_reason=finish_reason,
            usage=usage,
            text_delta=text_delta,
        )

         

"""
Example: ChatCompletion Response Structure from OpenRouter API : Non-Streaming Case

ChatCompletion(
    id='gen-1768474359-QXxuX0mtG19eIkiwTwhK',
    choices=[Choice(
        finish_reason='stop',
        index=0,
        logprobs=None,
        message=ChatCompletionMessage(
            content="Hello! 😊 I'm just a virtual assistant, so I don't have feelings, but I'm here and ready to help you with anything you need! How about you—how are you doing today? Anything on your mind or something I can assist with?",
            refusal=None,
            role='assistant',
            annotations=None,
            audio=None,
            function_call=None,
            tool_calls=None,
            reasoning=None
        ),
        native_finish_reason='stop'
    )],
    created=1768474359,
    model='mistralai/devstral-2512:free',
    object='chat.completion',
    service_tier=None,
    system_fingerprint=None,
    usage=CompletionUsage(
        completion_tokens=55,
        prompt_tokens=9,
        total_tokens=64,
        completion_tokens_details=CompletionTokensDetails(
            accepted_prediction_tokens=None,
            audio_tokens=None,
            reasoning_tokens=0,
            rejected_prediction_tokens=None
        ),
        prompt_tokens_details=PromptTokensDetails(
            audio_tokens=0,
            cached_tokens=0
        ),
        cost=0,
        is_byok=False,
        cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 'upstream_inference_completions_cost': 0}
    ),
    provider='Mistral'
)

Example for Streaming Case:

ChatCompletionChunk(
    id='gen-1768494229-3gVPLV0aSEmZHC35TbRj',
    choices=[Choice(
        delta=ChoiceDelta(
            content=' 😂',
            function_call=None,
            refusal=None,
            role='assistant',
            tool_calls=None
        ),
        finish_reason=None,
        index=0,
        logprobs=None,
        native_finish_reason=None
    )],
    created=1768494229,
    model='mistralai/devstral-2512:free',
    object='chat.completion.chunk',
    service_tier=None,
    system_fingerprint=None,
    usage=None,
    provider='Mistral'
)

Usage info is available at last chunk of the response.

ChatCompletionChunk(
    id='gen-1768494229-3gVPLV0aSEmZHC35TbRj',
    choices=[Choice(
        delta=ChoiceDelta(
            content='',
            function_call=None,
            refusal=None,
            role='assistant',
            tool_calls=None
        ),
        finish_reason=None,
        index=0,
        logprobs=None,
        native_finish_reason=None
    )],
    created=1768494229,
    model='mistralai/devstral-2512:free',
    object='chat.completion.chunk',
    service_tier=None,
    system_fingerprint=None,
    usage=CompletionUsage(
        completion_tokens=41,
        prompt_tokens=10,
        total_tokens=51,
        completion_tokens_details=CompletionTokensDetails(
            accepted_prediction_tokens=None,
            audio_tokens=None,
            reasoning_tokens=0,
            rejected_prediction_tokens=None
        ),
        prompt_tokens_details=PromptTokensDetails(
            audio_tokens=0,
            cached_tokens=0
        ),
        cost=0,
        is_byok=False,
        cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 'upstream_inference_completions_cost': 0}
    ),
    provider='Mistral'
)
"""
