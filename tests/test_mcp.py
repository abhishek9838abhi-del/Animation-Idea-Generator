"""Tests for MCP boundary, tool registry, and allowlist validation."""

import pytest
from app.mcp.registry import (
    tool_registry,
    ToolNotFoundError,
    ToolValidationError,
)
from app.mcp.boundary import SoundLibrarySearchTool


@pytest.mark.asyncio
async def test_mcp_allowlist_registered_tool():
    # Verify tool is registered
    tool = tool_registry.get_tool("sound_library_search")
    assert tool.name == "sound_library_search"

    # Execute registered tool
    result = await tool_registry.execute_tool(
        "sound_library_search",
        arguments={"query": "thunder", "category": "foley", "max_results": 2},
    )
    assert result["query"] == "thunder"
    assert len(result["results"]) <= 2


@pytest.mark.asyncio
async def test_mcp_unapproved_tool_rejection():
    with pytest.raises(ToolNotFoundError):
        tool_registry.get_tool("unapproved_shell_command")

    with pytest.raises(ToolNotFoundError):
        await tool_registry.execute_tool("unapproved_tool", arguments={})


@pytest.mark.asyncio
async def test_mcp_argument_validation_failure():
    with pytest.raises(ToolValidationError):
        # Query too short (min length is 2)
        await tool_registry.execute_tool(
            "sound_library_search",
            arguments={"query": "x"},
        )
