"""
This module defines the foundational building blocks for the Kraken Code tool system.

It provides the base classes and enums needed to define, validate, and execute tools
that the agent can use to interact with the environment.
"""

from pydantic.json_schema import model_json_schema
from pydantic import ValidationError
from dataclasses import Field
from pathlib import Path
from dataclasses import dataclass
from __future__ import annotations
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
    """
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

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

    @abc.abstractmethod
    async def execute(self, invocation: ToolInvokation) -> ToolResult:
        """
        Executes the tool's core logic.

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
                BaseModel(**params)
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

    
    
