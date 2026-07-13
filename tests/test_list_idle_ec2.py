"""Tests for the list_idle_ec2 tool and data loader."""
from __future__ import annotations

import pytest

from finops_agent.models import ResourceType
from mcp_server.data_loader import (
    AccountNotFoundError,
    load_account_resources,
)
from mcp_server.tools.list_idle_ec2 import (
    IDLE_CPU_THRESHOLD,
    list_idle_ec2_logic,
)


class TestDataLoader:
    def test_loads_synthetic_account(self) -> None:
        resources = load_account_resources("synthetic-001")
        assert len(resources) == 3

    def test_all_returned_are_resources(self) -> None:
        resources = load_account_resources("synthetic-001")
        assert all(r.resource_type == ResourceType.EC2 for r in resources)

    def test_missing_account_raises(self) -> None:
        with pytest.raises(AccountNotFoundError):
            load_account_resources("does-not-exist-999")


class TestListIdleEc2:
    def test_finds_two_idle_instances(self) -> None:
        """Fixture has exactly 2 idle EC2s (cpu < 5)."""
        idle = list_idle_ec2_logic("synthetic-001")
        assert len(idle) == 2

    def test_idle_instances_are_below_threshold(self) -> None:
        idle = list_idle_ec2_logic("synthetic-001")
        for r in idle:
            cpu = r.utilization_metrics["cpu_avg_14d"]
            assert cpu < IDLE_CPU_THRESHOLD

    def test_active_instance_excluded(self) -> None:
        """The active instance (cpu 65) must NOT be flagged idle."""
        idle = list_idle_ec2_logic("synthetic-001")
        idle_ids = {r.resource_id for r in idle}
        assert "i-fake-003" not in idle_ids  # active one

    def test_returns_expected_idle_ids(self) -> None:
        idle = list_idle_ec2_logic("synthetic-001")
        idle_ids = {r.resource_id for r in idle}
        assert idle_ids == {"i-fake-001", "i-fake-002"}

    def test_missing_account_raises(self) -> None:
        with pytest.raises(AccountNotFoundError):
            list_idle_ec2_logic("does-not-exist-999")


class TestMcpToolRegistration:
    def test_tool_registered(self) -> None:
        from mcp_server import server

        assert server.mcp is not None
        # The MCP tool wrapper returns JSON-serializable dicts
        result = server.list_idle_ec2("synthetic-001")
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)