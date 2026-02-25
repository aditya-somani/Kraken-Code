"""
This module handles the Terminal User Interface (TUI) for Kraken Code.

It uses the Rich library to provide a colorful, styled, and interactive
terminal experience, including custom themes for different agent states
and tool interactions.
"""

from distro import name
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.rule import Rule
from typing import Any
from rich.panel import Panel
from rich.table import Table

AGENT_THEME = Theme(
    {
        # General
        "info": "cyan",
        "warning": "yellow",
        "error": "bright_red bold",
        "success": "green",
        "dim": "dim",
        "muted": "grey50",
        "border": "grey35",
        "highlight": "bold cyan",
        # Roles
        "user": "bright_white bold",
        "assistant": "bright_blue",
        # Tools
        "tool": "bright_magenta bold",
        "tool.read": "cyan",
        "tool.write": "yellow",
        "tool.shell": "magenta",
        "tool.network": "bright_blue",
        "tool.memory": "green",
        "tool.mcp": "bright_cyan",
        # Code / blocks
        "code": "white",
    }
)

_console: Console | None = None
# This is global because we want to use the same console instance throughout the application.
# It would have multiple instances of console, there would be waste conditions for showing the output, 
# and there would be a lot of spaghetti mess in the terminal and problems which would overrun the user. 
# So it is the best practice for a good user experience to only have one singleton instance of console for us and for the user. 

def get_console() -> Console:
    """
    Retrieves the singleton Rich Console instance.

    Ensures that the entire application shares the same console state and theme,
    preventing output conflicts and maintaining a consistent look and feel.

    Returns:
        The global Console instance.
    """
    global _console
    if _console is None:
        _console = Console(theme=AGENT_THEME)
    return _console

class TUI:
    """
    Main Terminal UI renderer for the Kraken Code agent.
    
    Handles the visual presentation of assistant responses, rule lines,
    and formatted output blocks.
    """
    def __init__(
        self,
        console: Console | None = None
    ) -> None:
        """
        Initializes the TUI.

        Args:
            console: An optional console instance to use. If None, the global one is used.
        """
        self.console = _console or get_console()
        self._assistant_stream_open = False
        self._tool_args_by_call_id: dict[str, dict[str, Any]] = {} # Caches the arguments for each tool call by its ID.

    def begin_assitant(self) -> None:
        """
        Prepares the TUI for an incoming assistant message stream.

        Prints a rule line to visually separate the assistant's turn.
        """
        self.console.print()
        self.console.print(Rule(Text("Kraken", style="assistant")))
        self._assistant_stream_open = True

    def end_assistant(self) -> None:
        """
        Finalizes the assistant message stream.

        Ensures a clean break at the end of the streaming output.
        """
        if self._assistant_stream_open:
            self.console.print()
        self._assistant_stream_open = False

    def stream_assistant_messages(self, content: str) -> None:
        """
        Prints a chunk of text from the assistant without a newline.

        Args:
            content: The text delta to display.
        """
        self.console.print(content, end="", markup=False, emoji=True)

    def _ordered_args(self, name: str, args: dict[str, Any]) -> list[tuple[str, Any]]:
        """
        Orders the arguments of a tool call.

        Args:
            arguments: The arguments of the tool call.

        Returns:
            A list of tuples containing the ordered arguments.
        """
        _PREFERED_ORDER = {
            "read_file": ["path", "offset", "limit"]
        }

        preferred = _PREFERED_ORDER.get(name, [])
        ordered: list[tuple[str, Any]] = []
        seen = set() # all the tools we have seen so far
        
        for key in preferred:
            if key in args:
                ordered.append((key, args[key]))
                seen.add(key)

        remaining_keys = set(args.keys() - seen)
        ordered.extend((key, args[key] for key in remaining_keys))
        return ordered

    def _render_args_table(self,tool_name: str, args: dict[str, Any]) -> Table:
        """
        Renders the arguments of a tool call as a table.

        Args:
            tool_name: The name of the tool call.
            args: The arguments of the tool call.

        Returns:
            A table of arguments in a grid format (key: value).
        """
        table = Table.grid(padding=(0, 1))
        table.add_column(style="muted", justify="right", no_wrap=True)
        table.add_column(style="code", overflow="fold")

        for key, value in self._ordered_args(tool_name, args):
            table.add_row(key, value)

        return table

    def tool_call_start(
        self,
        call_id: str,
        name: str,
        tool_kind: str | None,
        arguments: dict[str, Any],
    ) -> None:
        """
        Handles the start of a tool call.

        Args:
            call_id: The unique identifier for the tool call.
            name: The name of the tool being called.
            tool_kind: The kind of tool being called.
            arguments: The arguments passed to the tool.
        """
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("• ", "muted"),
            (name, border_style + " bold"),
            (" ", "muted"),
            (f"#{call_id[:8]}", "muted"),   
        )

        panel = Panel(
            self._render_args_table(name, arguments),
            title=title,
            
        )
        
