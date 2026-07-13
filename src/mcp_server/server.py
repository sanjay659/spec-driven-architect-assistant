"""AWS FinOps MCP Server.

A single MCP server per domain (AWS cost optimization), exposing
tools that the FinOps agent can call. Tool logic lives in tools/;
this module only wires that logic into the MCP protocol.

Design reference: design.md Section 6 (MCP Design)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.health import health_check_logic

# Single MCP server instance for the AWS FinOps domain
mcp = FastMCP("aws-finops-mcp")


@mcp.tool()
def health_check() -> dict[str, str]:
    """Check that the AWS FinOps MCP server is running.

    Returns basic server status and metadata.
    """
    return health_check_logic()


def main() -> None:
    """Entry point: run the MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()