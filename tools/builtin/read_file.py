from utils.path import resolve_path, is_binary_file
from pydantic import BaseModel, Field
from tools.base import Tool, ToolKind, ToolInvokation, ToolResult
from utils.text import count_tokens, truncate_text
import os
from dotenv import load_dotenv

load_dotenv()

class ReadFileParams(BaseModel):
    """
    Parameters for the read_file tool.
    """
    path: str = Field(
        ...,
        description="Path to the file to read(relative to working directory or absolute)"
    )

    offset: int = Field(
        1, 
        ge=1, 
        description="Line number to start reading from (1-indexed). Defaults to 1"
    )

    limit: int | None = Field(
        None,
        ge=1,
        description="Maximum number of lines to read. Defaults to None (read until end of file)"
    )

class ReadFileTool(Tool):
    """
    Reads the contents of a text file. Returns the file content with line numbers.
    For large files, use offset and limit to read specific portions.
    Cannot read binary files (images, executables, etc.)
    """
    name = "read_file"
    description = (
        "Read the contents of a text file. Returns the file content with line numbers."
        "For large files, use offset and limit to read specific portions."
        "Cannot read binary files (images, executables, etc.) "
    )
    kind = ToolKind.READ
    schema = ReadFileParams

    MAX_FILE_SIZE = 1024 * 1024 * 10 # 10MB
    MAX_OUPUT_TOKENS = 25_000

    async def execute(self, invocation: ToolInvokation) -> ToolResult:
        """
        Executes the tool's core logic.

        Args:
            invocation: The parameters and environment context for this specific run.

        Returns:
            A ToolResult object containing the success/error status and output.
        """
        params = ReadFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(f"File not found at: {path}")

        if not path.is_file():
            return ToolResult.error_result(f"Path is not a file: {path}")

        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return ToolResult.error_result(
                f"File is too large: {file_size/(1024*1024):.1f}MB."
                f"Max allowed size is {self.MAX_FILE_SIZE/(1024*1024):.0f}MB"
            )

        if is_binary_file(path):
            file_size_mb = file_size / (1024 * 1024)
            size_str = f"{file_size_mb:.2f}MB" if file_size_mb >= 1 else f"{file_size / 1024:.2f}KB"
            return ToolResult.error_result(
                f"Cannot read binary file: {path.name} ({size_str})"
                f"This tool only reads text files."
            )

        try:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")
            
            lines = content.splitlines()
            total_lines = len(lines)

            if total_lines == 0:
                # We are sending this message because if we return just an empty string to the LLM, it wouldn't appropriately provide the context to the LLM that the file is empty. 
                # It would retry or do something else. It is better to couple a message like 'file is empty' so that the LLM can have better context. 
                return ToolResult.success_result(
                    "File is empty",
                    metadata={
                        "lines": 0,
                    }
                ) 

            start_idx = max(0, params.offset - 1)
            
            if params.limit is not None:
                end_idx = min(start_idx + params.limit, total_lines)
            else:
                end_idx = total_lines

            selected_lines = lines[start_idx:end_idx] # Didn't did "-1" because we want to include the last line as well. 
            formatted_lines: list[str] = []

            for i, line in enumerate(selected_lines, start=start_idx):
                formatted_lines.append(f"{i:6}: {line}")

            output = "\n".join(formatted_lines)
            token_count = count_tokens(output, model=os.getenv("MODEL"))

            truncated = False
            if token_count > self.MAX_OUPUT_TOKENS:
                output = truncate_text(
                    output,
                    self.MAX_OUPUT_TOKENS,
                    suffix=f"\n... (truncated {total_lines} total lines)"
                )
                truncated = True

            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"Lines {start_idx + 1} to {end_idx} of {total_lines}"
                )

            if metadata_lines:
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output

            return ToolResult.success_result(
                output=output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "shown_start": start_idx + 1,
                    "shown_end": end_idx,
                    "truncated": truncated,
                }
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Failed to read file: {str(e)}"
            )
        

            
        
