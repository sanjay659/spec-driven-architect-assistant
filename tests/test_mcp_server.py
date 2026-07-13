"""Tests for the AWS FinOps MCP server."""
from __future__ import annotations

from datetime import datetime

from mcp_server.tools.health import health_check_logic


class TestHealthCheck:
    def test_returns_ok_status(self) -> None:
        result = health_check_logic()
        assert result["status"] == "ok"

    def test_returns_server_name(self) -> None:
        result = health_check_logic()
        assert result["server"] == "aws-finops-mcp"

    def test_returns_version(self) -> None:
        result = health_check_logic()
        assert result["version"] == "0.1.0"

    def test_timestamp_is_valid_iso(self) -> None:
        result = health_check_logic()
        # Should parse without error and be timezone-aware (UTC)
        parsed = datetime.fromisoformat(result["timestamp"])
        assert parsed.tzinfo is not None


class TestServerImports:
    def test_server_module_imports(self) -> None:
        """Verify the MCP server module loads and registers the tool."""
        from mcp_server import server

        assert server.mcp is not None
        assert server.mcp.name == "aws-finops-mcp"