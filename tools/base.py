"""
This module defines the foundational building blocks for the Kraken Code `Tool` system.

It provides the base classes and enums needed to define, validate, and execute tools
that the agent can use to interact with the environment.
"""

# NOTE: Go to the end of file, for viewing schema accepted by OpenAI. 
# We keep the tool definition separate from the provider schema (OpenAI/Anthropic).
# 1. base.py defines the 'Contract' (What the tool does and what data it needs).
# 2. The LLM Client (e.g., openai_client.py) transforms this contract into a 
#    specific JSON format (the Schema) that the model understands.
#
# This allows us to switch LLM providers without touching the core tool logic.
# The 'parameters' field below uses Pydantic to provide a source of truth 
# from which ANY provider-specific schema can be generated.

from __future__ import annotations
from pydantic.json_schema import model_json_schema
from pydantic import ValidationError
from dataclasses import field
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Any
from enum import StrEnum
import abc

class ToolKind(StrEnum):
    """
    Categorizes tools based on their primary interaction type.

    This classification helps the agent understand the potential impact and 
    resource requirements of a tool before execution.
    """
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP = "mcp"

@dataclass
class ToolResult:
    """
    Encapsulates the outcome of a tool execution.

    Attributes:
        success: Whether the tool executed successfully.
        output: The primary textual output or result of the tool.
        error: A descriptive error message if success is False.
        metadata: Additional structured data returned by the tool (e.g., file stats).
        truncated: Whether the output was truncated.
    """
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False

    @classmethod
    def error_result(
        cls,
        error: str,
        output: str="",
        **kwargs
    ) -> ToolResult:
        """
        Creates an error result.

        Args:
            error: The error message.
            output: The output of the tool.
        Returns:
            ToolResult: An error result.
        """
        return cls(success=False, error=error, output=output, **kwargs)

    @classmethod
    def success_result(
        cls,
        output: str = "",
        **kwargs
    ) -> ToolResult:
        """
        Creates a success result.

        Args:
            output: The output of the tool.
            **kwargs: Additional keyword arguments.
        Returns:
            ToolResult: A success result.
        """
        return cls(success=True, output=output, error=None, **kwargs)

    # This is for formatting the output in a format the model will like/easy to parse.
    def to_model_output(self) -> str:
        """Formats the output for the model."""
        if self.success:
            return self.output
        else:
            return f"Error: {self.error}\n\nOutput:\n{self.output}"

@dataclass
class ToolInvokation:
    """
    Represents a specific request to run a tool with given parameters.

    Attributes:
        params: The arguments passed to the tool.
        cwd: The current working directory in which the tool should operate.
    """
    params: dict[str, Any]
    cwd: Path

@dataclass
class ToolConfirmation:
    tool_name: str
    params: dict[str, Any]
    description: str
    

class Tool(abc.ABC):
    """
    The abstract base class for all tools in the Kraken Code system.

    Each tool must define its name, description, schema for validation,
    and the logic for its execution.

    Attributes:
        name: The unique identifier for the tool.
        description: A human-readable (and LLM-readable) description of what the tool does.
        kind: The category of the tool (READ, WRITE, etc.).
    """
    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        """Initializes the tool instance."""
        pass

    @property
    def schema(self) -> dict[str, Any] | type["BaseModel"]:
        """
        Defines the expected parameter structure for the tool.

        Returns:
            Either a Pydantic BaseModel class for internal tools or a 
            dictionary representing a JSON schema for external MCP tools.
        """
        # BaseModel/Pydantic is when we will be defining our own schema for MCP tools -> in-built tools.
        # dict[str, Any] is when we will be calling external MCP ones, as they will be output in JSON format not pydantic model.
        # Due to the fact that we are using pydantic models, we can use pydantic validators to validate the params.
        raise NotImplementedError("The tool must define schema property or class attribute.")

    @abc.abstractmethod # Method must be implemented by subclasses.
    async def execute(self, invocation: ToolInvokation) -> ToolResult:
        """
        Executes the tool's core logic.
        Must be implemented by subclasses.

        Args:
            invocation: The parameters and environment context for this specific run.

        Returns:
            A ToolResult object containing the success status and output.
        """
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """
        Validates the provided parameters against the tool's schema.

        Args:
            params: A dictionary of parameters to validate.

        Returns:
            A list of error messages. If empty, validation passed.
        """
        # Error handling for pydantic models
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                schema(**params)
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = '.'.join(str(x) for x in error.get("loc", []))
                    msg = error.get("msg", "Validation Error")
                    errors.append(f"Parameter '{field}': {msg}")

                return errors
            except Exception as e:
                return [str(e)]

        # Error handling for dict[str, Any] -> Will be done by OpenAI API SDK by - Itself.  
        return []

    def is_mutating(self, params: dict[str, Any]) -> bool:
        """
        Checks if the tool execution will modify the state of the system.

        Args:
            params: The parameters for the tool call.

        Returns:
            True if the tool is of a mutating kind (WRITE, SHELL, etc.).
        """
        return self.kind in (
            ToolKind.WRITE, 
            ToolKind.SHELL, 
            ToolKind.NETWORK, 
            ToolKind.MEMORY
        )

    async def get_confirmation(self, invocation: ToolInvokation) -> ToolConfirmation | None:
        """
        Asks the user for confirmation before executing a mutating tool.

        Args:
            invocation: The tool invocation request.

        Returns:
            A ToolConfirmation object indicating whether the user approved or denied the execution then None.
        """
        if not self.is_mutating(invocation.params):
            return None

        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=self.description,
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """
        Converts the tool's schema to a format compatible with the OpenAI API.

        Returns:
            A dictionary representing the tool's schema in OpenAI format.
        """
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = model_json_schema(schema, mode='serialization')
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                }
            }

        if isinstance(schema, dict):
            result = {
                "name": self.name,
                "description": self.description
            }

            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema

        raise ValueError(f"Invalid schema type for tool {self.name}: {type(schema)}")

    
"""
tools: array of map[unknown]
A list of tool definitions that the model should be allowed to call.

For the Chat Completions API, the list of tool definitions might look like:

[
  { 
    "type": "function", 
    "function": { 
        "name": "get_weather",
    } 
  },
  { 
    "type": "function", 
    "function": { 
        "name": "get_time" 
    } 
  }
]
"""
