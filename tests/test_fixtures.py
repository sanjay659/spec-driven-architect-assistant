"""Tests for synthetic test fixtures."""
import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Helper to load a JSON fixture file."""
    path = FIXTURES_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestSyntheticAccount001:
    """Verify synthetic_account_001 fixture is well-formed."""

    @pytest.fixture(scope="class")
    def account_data(self) -> dict:
        return load_fixture("synthetic_account_001")

    def test_account_metadata(self, account_data: dict) -> None:
        """Account has required top-level metadata."""
        assert account_data["account_id"] == "synthetic-001"
        assert account_data["region"] == "us-east-1"
        assert "resources" in account_data

    def test_resource_count(self, account_data: dict) -> None:
        """Account has expected number of resources."""
        assert len(account_data["resources"]) == 3

    def test_all_resources_have_required_fields(self, account_data: dict) -> None:
        """Every resource has the fields our domain model expects."""
        required_fields = {
            "resource_id",
            "resource_type",
            "region",
            "tags",
            "monthly_cost",
            "utilization_metrics",
        }
        for resource in account_data["resources"]:
            assert required_fields.issubset(resource.keys()), (
                f"Resource {resource.get('resource_id')} missing fields: "
                f"{required_fields - set(resource.keys())}"
            )

    def test_two_idle_ec2_instances(self, account_data: dict) -> None:
        """Fixture must contain 2 idle EC2s for M1 testing."""
        idle_ec2s = [
            r
            for r in account_data["resources"]
            if r["resource_type"] == "ec2"
            and r["utilization_metrics"]["cpu_avg_14d"] < 5.0
        ]
        assert len(idle_ec2s) == 2, "Expected exactly 2 idle EC2 instances for M1 testing"

    def test_one_active_ec2(self, account_data: dict) -> None:
        """Fixture must contain 1 active EC2 (control case)."""
        active_ec2s = [
            r
            for r in account_data["resources"]
            if r["resource_type"] == "ec2"
            and r["utilization_metrics"]["cpu_avg_14d"] >= 50.0
        ]
        assert len(active_ec2s) == 1, "Expected exactly 1 active EC2 as control case"

    def test_monthly_cost_is_positive(self, account_data: dict) -> None:
        """All resources have non-negative cost."""
        for resource in account_data["resources"]:
            assert resource["monthly_cost"] >= 0

    def test_production_resource_exists(self, account_data: dict) -> None:
        """At least one resource is tagged production (for safety validation later)."""
        prod_resources = [
            r for r in account_data["resources"]
            if r.get("tags", {}).get("Environment") == "production"
        ]
        assert len(prod_resources) >= 1, "Fixture must include a production resource"