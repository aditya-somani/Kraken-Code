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
        return len(tokenizer(text or ""))
        
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

def truncate_text(
    text: str,
    max_tokens: int,
    model: str,
    suffix: str = "\n...[Truncated]",
    preserve_lines: bool = True
) -> str:
    """
    Truncates text to a maximum token limit.

    Args:
        text: The text to truncate.
        max_tokens: The maximum number of tokens.
        model: The model name.
        suffix: The suffix to append to truncated text.
        preserve_lines: Whether to preserve lines.

    Returns:
        The truncated text.
    """
    current_tokens = count_tokens(text, model)
    if current_tokens <= max_tokens:
        return text

    suffix_tokens = count_tokens(suffix, model)
    target_tokens = max_tokens - suffix_tokens

    if target_tokens <= 0:
        return suffix.strip()    

    if preserve_lines:
        return _truncate_by_lines(text, target_tokens, model, suffix)
    else:
        return _truncate_by_chars(text, target_tokens, model, suffix)

def _truncate_by_lines(text: str, target_tokens: int, model: str, suffix: str) -> str:
    """
    Truncates text by lines to a maximum token limit.

    Args:
        text: The text to truncate.
        target_tokens: The maximum number of tokens.
        model: The model name.
        suffix: The suffix to append to truncated text.

    Returns:
        The truncated text.
    """
    lines = text.split('\n')
    result_lines: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line + '\n', model)
        if current_tokens + line_tokens >= target_tokens:
            break
        result_lines.append(line)
        current_tokens += line_tokens

    if not result_lines:
        # Fallback to character truncation if have no complete line. 
        return _truncate_by_chars(text, target_tokens, model, suffix)
    
    return '\n'.join(result_lines) + suffix

def _truncate_by_chars(text: str, target_tokens: int, model: str, suffix: str) -> str:
    """
    Truncates text by characters to a maximum token limit.
    Uses binary search for efficiency.

    Args:
        text: The text to truncate.
        target_tokens: The maximum number of tokens.
        model: The model name.
        suffix: The suffix to append to truncated text.

    Returns:
        The truncated text.
    """
    # Binary search for the right length. 
    low, high = 0, len(text)
    
    while low < high:
        mid = (low + high + 1) // 2
        if count_tokens(text[:mid], model) <= target_tokens:
            low = mid
        else:
            high = mid - 1

    return text[:low] + suffix
        


