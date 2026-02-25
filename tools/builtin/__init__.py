from tools.builtin.read_file import ReadFileTool
from tools.base import Tool

__all__ = [
    'ReadFileTool'
]

def get_builtin_tools() -> list[Tool]:
    """
    Returns a list of built-in tools.

    Returns:
        A list of built-in tools.
    """
    return [
        ReadFileTool
    ]