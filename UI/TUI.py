# TUI.py: The user interface (UI) layer. It handles displaying messages to the user and capturing their input.
# This is the "face" of the application, It renders the output of the agent to the user.
# Rich is a Python library for writing rich text (with color and style) to the terminal, 
# and for displaying advanced content such as tables, markdown, and syntax highlighted code.

from rich.console import Console
from rich.theme import Theme

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
        "user": "bright_blue bold",
        "assistant": "bright_white",
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
    global _console
    if _console is None:
        _console = Console(theme=AGENT_THEME)
    return _console

class TUI:
    # Main Terminal UI renderer class
    def __init__(
        self,
        console: Console | None = None
    ) -> None:
        self.console = _console or get_console()

    def stream_assistant_messages(self, content: str) -> None:
        self.console.print(content, end="", markup=False, emoji=True)
