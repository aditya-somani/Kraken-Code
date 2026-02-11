"""
This module handles the Terminal User Interface (TUI) for Kraken Code.

It uses the Rich library to provide a colorful, styled, and interactive
terminal experience, including custom themes for different agent states
and tool interactions.
"""

from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.rule import Rule

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
