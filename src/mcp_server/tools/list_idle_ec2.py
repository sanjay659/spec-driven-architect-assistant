"""Tool: list_idle_ec2 — detect idle EC2 instances.

Pure logic, separated from MCP wiring (testable without transport).

Design reference:
- design.md Section 6.3 (tool)
- requirements.md AC-03 (idle detection, CPU < threshold)
"""
from __future__ import annotations

from mcp_server.data_loader import load_account_resources
from finops_agent.models import Resource, ResourceType

# Idle detection thresholds (requirements AC-03)
IDLE_CPU_THRESHOLD = 5.0
IDLE_LOOKBACK_METRIC = "cpu_avg_14d"


def _is_idle_ec2(resource: Resource) -> bool:
    """A resource is an idle EC2 if it is EC2 and its avg CPU is below threshold."""
    if resource.resource_type != ResourceType.EC2:
        return False
    cpu = resource.utilization_metrics.get(IDLE_LOOKBACK_METRIC)
    if cpu is None:
        # No metric data available -> cannot classify as idle (EC-04)
        return False
    return cpu < IDLE_CPU_THRESHOLD


def list_idle_ec2_logic(account_id: str) -> list:
    """Return all idle EC2 instances for the given account.

    Args:
        account_id: The AWS account identifier (v1: fixture id).

    Returns:
        List of Resource objects that are idle EC2 instances.
        Empty list if none found or account has no resources.
    """
    resources = load_account_resources(account_id)
    return [r for r in resources if _is_idle_ec2(r)]