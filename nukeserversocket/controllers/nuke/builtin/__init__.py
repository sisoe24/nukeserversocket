"""The panel's own MCP tools. Each module imports nuke, so import this inside Nuke only."""
from __future__ import annotations

from typing import Dict

from ....tools import Tool


def builtin_tools() -> Dict[str, Tool]:
    from .graph import GRAPH_TOOL
    from .vision import VISION_TOOL
    return {t.name: t for t in (VISION_TOOL, GRAPH_TOOL)}
