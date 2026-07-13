"""AWS FinOps MCP Server.

A single MCP server per domain (AWS cost optimization), exposing
tools that the FinOps agent can call. Tool logic lives in tools/;
this module only wires that logic into the MCP protocol.

Design reference: design.md Section 6 (MCP Design)
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.health import health_check_logic
from mcp_server.tools.list_idle_ec2 import list_idle_ec2_logic

# Single MCP server instance for the AWS FinOps domain
mcp = FastMCP("aws-finops-mcp")


@mcp.tool()
def health_check() -> dict[str, str]:
    """Check that the AWS FinOps MCP server is running."""
    return health_check_logic()


@mcp.tool()
def list_idle_ec2(account_id: str) -> list[dict[str, Any]]:
    """List idle EC2 instances for an AWS account.

    An instance is considered idle if its 14-day average CPU
    utilization is below 5%.

    Args:
        account_id: The AWS account identifier to audit.

    Returns:
        A list of idle EC2 resources with their details.
    """
    idle_resources = list_idle_ec2_logic(account_id)
    # MCP tools return JSON-serializable data, so dump the models to dicts
    return [r.model_dump(mode="json") for r in idle_resources]


def main() -> None:
    """Entry point: run the MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()