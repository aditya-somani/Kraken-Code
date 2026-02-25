from pathlib import Path
from typing import Any
from tools.base import Tool, ToolResult, ToolInvokation
from tools.builtin import ReadFileTool, get_builtin_tools
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    A registry of tools.
    """
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Registers a tool.

        Args:
            tool: The tool to register.

        Returns:
            None
        """
        if tool.name in self._tools:
            logger.warning(f"Overwrite existing tool: {tool.name}")
            
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> bool:
        """
        Unregisters a tool.

        Args:
            name: The name of the tool to unregister.

        Returns:
            True if the tool was unregistered, False otherwise.
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def get_tools(self) -> list[Tool]:
        """
        Returns a list of tools.

        Returns:
            A list of tools.
        """
        tools: list[Tool] = []
        for tool in self._tools.values():
            tools.append(tool)
        return tools

    def get_schemas(self) -> list[dict[str, Any]]:
        """
        Returns a list of tool schemas.

        Returns:
            A list of tool schemas.
        """
        return [tool.to_openai_schema() for tool in self.get_tools()]

    def get(self, name: str) -> Tool | None:
        """
        Retrieves a tool by name.

        Args:
            name: The name of the tool to retrieve.

        Returns:
            The tool if found, None otherwise.
        """
        if name in self._tools:
            return self._tools[name]

        return None

    async def invoke(
        self,
        name: str,
        params: dict[str, Any],
        cwd: Path
    ) -> ToolResult:
        """
        Invokes a tool by name.

        Args:
            name: The name of the tool to invoke.
            params: The parameters to pass to the tool.
            cwd: The current working directory.

        Returns:
            The result of the tool execution.
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                f"Unknown tool: {name}",
                metadata={"tool_name": name}
            )

        validation_errors = tool.validate_params(params)
        if validation_errors:
            return ToolResult.error_result(
                f"Invalid parameters for tool {name}: {'; '.join(validation_errors)}",
                metadata={
                    "tool_name": name,
                    "validation_errors": validation_errors
                }
            )
        
        invocation = ToolInvokation(
            params=params,
            cwd=cwd
        )
        try:
            result = await tool.execute(invocation)
        except Exception as e:
            result = ToolResult.error_result(
                f"Error executing tool {name}: {str(e)}",
                metadata={
                    "tool_name": name,
                }
            )
        return result

def create_default_registry() -> ToolRegistry:
    """
    Creates a default tool registry with all built-in tools.

    Returns:
        A ToolRegistry instance.
    """
    registry = ToolRegistry()
    
    for tool_class in get_builtin_tools():
        registry.register(tool_class())
        
    return registry
