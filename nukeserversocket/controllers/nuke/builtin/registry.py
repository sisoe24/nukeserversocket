"""The list of built-in tools. Each tool module imports nuke, so call this inside Nuke only."""
from __future__ import annotations

from ....tools import Tool


def builtin_tools() -> dict[str, Tool]:
    """The built-in tools."""
    from .graph import GRAPH_TOOL
    from .stats import STATS_TOOL
    from .vision import VISION_TOOL
    return {t.name: t for t in [VISION_TOOL, GRAPH_TOOL, STATS_TOOL]}
