"""Health check tool logic (pure, testable, no MCP dependency).

Design reference: design.md Section 6.3 (MCP server design)
"""
from __future__ import annotations

from datetime import datetime, timezone


def health_check_logic() -> dict[str, str]:
    """Return server health status.

    Kept separate from the MCP registration so it can be
    unit-tested without starting the MCP transport.
    """
    return {
        "status": "ok",
        "server": "aws-finops-mcp",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }