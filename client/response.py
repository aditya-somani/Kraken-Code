# Schema Layer for Responses
# This file is created to standardize and structure the way the application handles responses from Large Language Models (LLMs), 
# especially when dealing with both streaming and non-streaming outputs

# In a nutshell, We are creating these structures because we want to standardize how information is captured, moved, and saved.
# As each LLM has its own way of responding, we need to standardize the way we handle the responses.

# To understand the intuition behind choosing such structure, see at the bottom of the file or the LLM response in `notebooks/test01.ipynb`.

# Imports
from __future__ import annotations # This is so that we can use TokenUsage in its own __add__ method.
from dataclasses import dataclass
from enum import StrEnum

# TextDelta is a class that represents a tiny chunk of text arriving from the LLM. + For future use, we can add more fields to this class.
@dataclass
class TextDelta:
    content: str

    def __str__(self) -> str: # So, now not needed to use TextDelta.content to print the content.
        return self.content
    #In Python, __str__ is a Magic Method (also called a Dunder method). 
    # It tells Python: "Whenever someone tries to print(object) or convert this object to a string using str(object), 
    # return this specific text("Hello, world!") instead of the default gibberish i.e. something like <response.TextDelta object at 0x7f81b0>"

# Labels that tell the system exactly what kind of event is happening right now (e.g., text is arriving, or an error occurred).
class StreamEventType(StrEnum):
    TEXT_DELTA = "text_delta" # Tiny chunks of text arriving
    MESSAGE_COMPLETE = "message_complete" # The full response has arrived
    ERROR = "error" # An error occurred 

# TokenUsage is a class that represents the usage/statistics of tokens by the LLM.
@dataclass
class TokenUsage:
    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    # This is so that we can add two TokenUsage objects together. => To get the total usage of tokens.
    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            completion_tokens=self.completion_tokens + other.completion_tokens,
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )


# Intuition behind making `StreamEvent`
# When interacting with an LLM, the responses can vary. 
# You might get a full response  at once (non-streaming) or chunks of text over time (streaming) as LLMs are auto-regressive. 
# Additionally, the response might contain just text, or it might include tool calls, or even an error. 
# StreamEvent acts as a unified schema or class definition for any event that comes from the model. 
# This makes it easier to process and manage different types of responses consistently.

@dataclass
class StreamEvent:
    type: StreamEventType
    text_delta: TextDelta | None = None # None in cases like when there is a tool call and such.
    error: str | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None

    @classmethod
    def stream_error(cls, error: str) -> StreamEvent:
        return cls(
            type=StreamEventType.ERROR,
            error=error
        )

    @classmethod
    def stream_text(cls, content: str) -> StreamEvent:
        return cls(
            type=StreamEventType.TEXT_DELTA,
            text_delta=TextDelta(content=content),
        )

    @classmethod
    def stream_message_complete(
        cls,
        finish_reason: str,
        usage: TokenUsage,
        text_delta: TextDelta | None = None
    ) -> StreamEvent:
        return cls(
            type=StreamEventType.MESSAGE_COMPLETE,
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
