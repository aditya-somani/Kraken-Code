"""
This module handles the Terminal User Interface (TUI) for Kraken Code.

It uses the Rich library to provide a colorful, styled, and interactive
terminal experience, including custom themes for different agent states
and tool interactions.
"""

# Standard library imports
from typing import Any
from pathlib import Path
import re
import os
import dotenv

# Rich library imports
from rich import box
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.console import Group

# Local application imports
from utils.path import display_path_rel_to_cwd
from utils.text import truncate_text

dotenv.load_dotenv()

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
        self.cwd: Path = Path.cwd()

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
        ordered.extend((key, args[key]) for key in remaining_keys)
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
            ("● ", "muted"), # • 
            (name, f"{border_style} bold"),
            (" ", "muted"),
            (f"#{call_id[:10]}", "muted"),   
        )

        display_args = dict(arguments)
        for key in ("path", "cwd"):
            val = display_args.get(key)
            if isinstance(val, str) and self.cwd:
                display_args[key] = str(display_path_rel_to_cwd(val, self.cwd))


        panel = Panel(
            self._render_args_table(name, display_args) if display_args else Text("No arguments", style="muted"),
            title=title,
            title_align="left",
            box=box.ROUNDED,
            padding=(1,2),
            border_style=border_style,
            subtitle=Text("running...", style="muted"),
            subtitle_align="right"
        )
        self.console.print() # print a newline
        self.console.print(panel)

    def _extract_read_file_code(self, text: str) -> tuple[int, str] | None:
        """
        Extracts the code from the read_file tool output.\n
        The output is in the format of "Showing lines x-y of z\\n\\n 1| <code>\\n 2| <code>\\n ...\\n y| <code>"

        Args:
            text: The text to extract the code from. This is the output of the read_file tool.

        Returns:
            A tuple containing the start line number and the code. If the code is not found, returns None.
        """
        # Structure -> "Showing lines x-y of z\n\n 1| <code>\n 2| <code>\n ...\n y| <code>" -> From read_file tool.
        body = text
        header_match = re.match(r"^Showing lines (\d+)-(\d+) of (\d+)\n\n", text) # (\d+) is a capturing group for the numbers like 1, 11, 111, etc.

        if header_match:
            body = body[header_match.end():]

        code_lines: list[str] = []
        start_line: int | None = None

        for line in body.splitlines():
            # <number> | <code> -> Example: "1| print('Hello, world!')"
            # Also indentation matters, so we can't ignore the spaces.
            # -----------------------------------------------------------
            # Example line: "   12| some code"
            # ^\s*     -> match any leading spaces at line start
            # (\d+)    -> match one or more digits (the line number), as it's in (parentheses) so it's a capturing group. It will be used to extract the line number. -> Group 1.
            # \|       -> match the literal '|' character
            # (.*)     -> match the rest of the line (the code/text), used to extract code/text -> Group 2.
            # $        -> end of line
            m = re.match(r'^\s*(\d+)\|(.*)$', line)
            if not m:
                return None
            line_no = int(m.group(1))
            if start_line is None:
                start_line = line_no
            code_lines.append(m.group(2))
        
        if start_line is None:
            return None
        
        return start_line, "\n".join(code_lines)
    
    def _guess_programming_language(self, path: str | None) -> str:
        """
        Guesses the programming language of a file based on its path(suffix).

        Args:
            path: The path to the file.

        Returns:
            The programming language of the file. If the language is not found, returns "text".
        """
        if not path:
            return "text"
        suffix = Path(path).suffix.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".toml": "toml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".hpp": "cpp",
            ".css": "css",
            ".html": "html",
            ".xml": "xml",
            ".sql": "sql",
        }.get(suffix, "text")

    def tool_call_complete(
        self,
        call_id: str,
        name: str,
        tool_kind: str | None,
        success: bool,
        output: str,
        error: str | None,
        metadata: dict[str, Any] | None,
        truncated: bool,
    ) -> None:
        """
        Handles the completion of a tool call.

        Args:
            call_id: The unique identifier for the tool call.
            name: The name of the tool being called.
            tool_kind: The kind of tool being called.
            success: Whether the tool call was successful.
            output: The output of the tool call.
            error: The error of the tool call.
            metadata: The metadata of the tool call.
            truncated: Whether the tool call was truncated.
        """
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"
        status_icon = "✓" if success else "✗"
        status_style = "success" if success else "error"

        title = Text.assemble(
            (f"{status_icon} ", f"{status_style}"),
            (name, f"{border_style} bold"),
            (" ", "muted"),
            (f"#{call_id[:10]}", "muted"),   
        )

        # Get path from metadata
        primary_path = None
        blocks = []
        if isinstance(metadata, dict) and isinstance(metadata.get("path"), str):
            primary_path = metadata.get("path")

        if name == "read_file" and success:
            if primary_path:
                start_line, code = self._extract_read_file_code(output)

                shown_start = metadata.get("shown_start")
                shown_end = metadata.get("shown_end")
                total_lines = metadata.get("total_lines")

                programming_language = self._guess_programming_language(primary_path)

                header_parts = [display_path_rel_to_cwd(primary_path, self.cwd)]
                header_parts.append(" • ")

                if shown_start and shown_end and total_lines:
                    header_parts.append(f"lines {shown_start}-{shown_end} of {total_lines}")

                header = " ".join(header_parts)
                blocks.append(Text(header, style="muted"))
                blocks.append(Syntax(
                    code=code,
                    lexer=programming_language,
                    theme="github-dark",
                    line_numbers=True,
                    start_line=start_line,
                    word_wrap=True
                ))
            else:
                output_display = truncate_text(
                    text=output,
                    max_tokens=250,
                    model=os.getenv("MODEL"),
                )
                blocks.append(Syntax(
                    code=output_display,
                    lexer="text",
                    theme="github-dark",
                    line_numbers=True,
                    word_wrap=True
                ))

        if truncated:
            blocks.append(Text("Note: The output was truncated", style="warning"))

        panel = Panel(
            Group(
                *blocks
            ),
            title=title,
            title_align="left",
            subtitle=Text("done • " if success else "failed • ", style=status_style),
            subtitle_align="right",
            box=box.ROUNDED,
            padding=(1,2),
            border_style=border_style,
        )
        self.console.print()
        self.console.print(panel)