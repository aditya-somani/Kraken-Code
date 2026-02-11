"""
This module provides text processing utilities for Kraken Code.

It includes functions for tokenizing text and counting tokens, which are essential
for managing LLM context windows and calculating costs.
"""

import tiktoken

def get_tokenizer(model: str):
    """
    Retrieves the appropriate tokenizer for a given model.

    Attempts to find a model-specific encoding using tiktoken. Falls back 
    to the "cl100k_base" encoding (used by GPT-4 and others) if the specific 
    model is not recognized.

    Args:
        model: The name of the model (e.g., "gpt-4", "claude-3-opus").

    Returns:
        The encode method of the selected tokenizer.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return encoding.encode 
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode

def count_tokens(text: str, model: str) -> int:
    """
    Calculates the exact or estimated token count for a text string.

    Uses the model-specific tokenizer if possible, otherwise falls back
    to a rough estimation based on character count.

    Args:
        text: The string to count tokens for.
        model: The model name to determine the tokenization scheme.

    Returns:
        The number of tokens in the text.
    """
    tokenizer = get_tokenizer(model)
    if tokenizer:
        return len(tokenizer(text))
        
    return estimate_tokens(text)

def estimate_tokens(text: str) -> int:
    """
    Provides a rough estimate of the number of tokens in a string.

    Uses the heuristic that 1 token is approximately 4 characters.

    Args:
        text: The string to estimate tokens for.

    Returns:
        The estimated token count.
    """
    return max(1, int(len(text)//4))

