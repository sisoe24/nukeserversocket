"""The panel's own MCP tools. Each module imports nuke, so import this inside Nuke only."""
from __future__ import annotations

from ....tools import Tool


def builtin_tools(vision: bool) -> dict[str, Tool]:
    """The built-in tools; nuke_vision only with `vision`, as only it sends pixels."""
    from .graph import GRAPH_TOOL
    from .stats import STATS_TOOL
    from .vision import VISION_TOOL
    tools = [VISION_TOOL] if vision else []
    return {t.name: t for t in [*tools, GRAPH_TOOL, STATS_TOOL]}
