"""Tool Registry and Execution Allowlist for Model Context Protocol (MCP) boundary."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    """Base exception for MCP tool issues."""


class ToolNotFoundError(MCPToolError):
    """Raised when an unapproved or unknown tool is requested."""


class ToolValidationError(MCPToolError):
    """Raised when tool arguments fail schema validation."""


class ToolPermissionError(MCPToolError):
    """Raised when an action requires explicit user permission that was not granted."""


class BaseTool(ABC):
    """Abstract base class for all allowlisted server-side tools."""

    name: str
    description: str
    args_schema: Type[BaseModel]
    requires_user_confirmation: bool = False

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool logic and return structured result."""
        pass

    def to_nvidia_tool_spec(self) -> Dict[str, Any]:
        """Translates the tool definition into standard OpenAI/NVIDIA function calling format."""
        schema = self.args_schema.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }


class ToolRegistry:
    """Enforces an allowlist of permitted tools; prevents arbitrary tool discovery or invocation."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Registers a tool in the local allowlist."""
        self._tools[tool.name] = tool
        logger.info("Registered allowlisted MCP tool: %s", tool.name)

    def get_tool(self, tool_name: str) -> BaseTool:
        """Retrieves a registered tool or raises ToolNotFoundError."""
        if tool_name not in self._tools:
            logger.warning("Rejected unapproved tool invocation attempt: '%s'", tool_name)
            raise ToolNotFoundError(f"Tool '{tool_name}' is not in the approved tool allowlist.")
        return self._tools[tool_name]

    def list_tool_specs(self) -> List[Dict[str, Any]]:
        """Returns the OpenAI/NVIDIA formatted specs of all allowlisted tools."""
        return [tool.to_nvidia_tool_spec() for tool in self._tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Validates arguments, checks permissions, and executes an allowlisted tool."""
        tool = self.get_tool(tool_name)

        # Check permissions for sensitive actions
        if tool.requires_user_confirmation and not user_confirmed:
            raise ToolPermissionError(
                f"Tool '{tool_name}' requires explicit user confirmation before execution."
            )

        # Validate arguments against Pydantic schema
        try:
            validated_args = tool.args_schema(**arguments)
        except ValidationError as e:
            logger.error("Argument validation failed for tool '%s': %s", tool_name, str(e))
            raise ToolValidationError(
                f"Invalid arguments for tool '{tool_name}': {e.errors()[0]['msg']}"
            ) from e

        # Execute
        try:
            return await tool.execute(**validated_args.model_dump())
        except Exception as e:
            logger.error("Execution failed for tool '%s': %s", tool_name, str(e))
            raise MCPToolError(f"Tool execution failed: {str(e)}") from e


# Global tool registry instance
tool_registry = ToolRegistry()
