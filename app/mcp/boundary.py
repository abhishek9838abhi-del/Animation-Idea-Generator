"""MCP Architectural Integration Boundary and Demonstration Tool."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from app.mcp.registry import BaseTool, tool_registry


# ---------------------------------------------------------------------------
# Example Tool: Sound Library Search Tool (Demonstration of extensible boundary)
# ---------------------------------------------------------------------------
class SoundSearchArgs(BaseModel):
    query: str = Field(..., min_length=2, max_length=100, description="Sound effect search term")
    category: str = Field(default="foley", description="Category: foley, ambience, or music")
    max_results: int = Field(default=3, ge=1, le=5)


class SoundLibrarySearchTool(BaseTool):
    """
    Allowlisted tool demonstrating future MCP integration for finding
    curated, royalty-free audio cues and foley for animation scenes.
    """

    name = "sound_library_search"
    description = "Searches a curated sound library for creative commons audio cues suited for animation scenes."
    args_schema = SoundSearchArgs
    requires_user_confirmation = False

    async def execute(self, query: str, category: str = "foley", max_results: int = 3) -> Dict[str, Any]:
        # Simulated safe sound library results
        mock_library = {
            "thunder": [
                {"name": "Distant Low Thunder", "duration": "3.5s", "license": "CC0"},
                {"name": "Sharp Thunderclap", "duration": "1.8s", "license": "CC-BY"},
            ],
            "wind": [
                {"name": "Gentle Meadow Breeze", "duration": "5.0s", "license": "CC0"},
                {"name": "Whistling Gust", "duration": "2.2s", "license": "CC0"},
            ],
            "footsteps": [
                {"name": "Light Sneaker Taps on Wood", "duration": "2.0s", "license": "CC0"},
                {"name": "Heavy Cartoon Thud", "duration": "0.8s", "license": "CC0"},
            ],
        }

        # Match query keywords
        results = []
        q_lower = query.lower()
        for key, sounds in mock_library.items():
            if key in q_lower or q_lower in key:
                results.extend(sounds)

        if not results:
            results = [
                {"name": f"Generic {query.title()} Effect", "duration": "2.0s", "license": "CC0"}
            ]

        return {
            "query": query,
            "category": category,
            "results": results[:max_results],
        }


# Register the demonstration tool into the allowlist
tool_registry.register_tool(SoundLibrarySearchTool())
