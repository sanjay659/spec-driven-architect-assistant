"""Tests for core domain models."""
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from finops_agent.models import (
    AuditRequest,
    AuditResult,
    Recommendation,
    RecommendationAction,
    Resource,
    ResourceType,
    RiskLevel,
    ValidationStatus,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestResource:
    def test_valid_resource(self) -> None:
        r = Resource(
            resource_id="i-fake-001",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            monthly_cost=Decimal("50.00"),
        )
        assert r.resource_id == "i-fake-001"
        assert r.resource_type == ResourceType.EC2
        assert r.monthly_cost == Decimal("50.00")

    def test_negative_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Resource(
                resource_id="i-bad",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                monthly_cost=Decimal("-1"),
            )

    def test_blank_resource_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Resource(
                resource_id="   ",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                monthly_cost=Decimal("10"),
            )

    def test_invalid_resource_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Resource(
                resource_id="i-x",
                resource_type="lambda",  # not in enum
                region="us-east-1",
                monthly_cost=Decimal("10"),
            )

    def test_resource_is_frozen(self) -> None:
        r = Resource(
            resource_id="i-x",
            resource_type=ResourceType.EC2,
            region="us-east-1",
            monthly_cost=Decimal("10"),
        )
        with pytest.raises(ValidationError):
            r.monthly_cost = Decimal("20")  # frozen — should fail


class TestRecommendation:
    def test_valid_recommendation(self) -> None:
        rec = Recommendation(
            finding_id="f-1",
            action=RecommendationAction.STOP,
            rationale="Instance idle for 14 days",
            estimated_savings=Decimal("50"),
            risk_level=RiskLevel.LOW,
            priority=1,
        )
        assert rec.action == RecommendationAction.STOP
        assert rec.validation_status == ValidationStatus.PENDING
        assert rec.recommendation_id  # auto-generated UUID

    def test_priority_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                finding_id="f-1",
                action=RecommendationAction.STOP,
                rationale="x",
                estimated_savings=Decimal("10"),
                risk_level=RiskLevel.LOW,
                priority=0,  # invalid
            )


class TestAuditResult:
    def test_total_savings_computed(self) -> None:
        recs = [
            Recommendation(
                finding_id="f-1",
                action=RecommendationAction.STOP,
                rationale="idle",
                estimated_savings=Decimal("50"),
                risk_level=RiskLevel.LOW,
                priority=1,
            ),
            Recommendation(
                finding_id="f-2",
                action=RecommendationAction.STOP,
                rationale="idle",
                estimated_savings=Decimal("30"),
                risk_level=RiskLevel.LOW,
                priority=2,
            ),
        ]
        result = AuditResult(request_id="req-1", recommendations=recs)
        assert result.total_estimated_savings == Decimal("80")

    def test_empty_result_zero_savings(self) -> None:
        result = AuditResult(request_id="req-1")
        assert result.total_estimated_savings == Decimal("0")


class TestFixtureLoadsIntoResource:
    """Integration: synthetic fixture (T-A-03) maps into Resource model."""

    def test_fixture_resources_validate(self) -> None:
        with (FIXTURES_DIR / "synthetic_account_001.json").open(encoding="utf-8") as f:
            data = json.load(f)

        resources = [Resource.model_validate(r) for r in data["resources"]]
        assert len(resources) == 3
        assert all(isinstance(r, Resource) for r in resources)

    def test_two_idle_from_fixture(self) -> None:
        with (FIXTURES_DIR / "synthetic_account_001.json").open(encoding="utf-8") as f:
            data = json.load(f)

        resources = [Resource.model_validate(r) for r in data["resources"]]
        idle = [
            r for r in resources
            if r.utilization_metrics.get("cpu_avg_14d", 100) < 5.0
        ]
        assert len(idle) == 2


class TestAuditRequest:
    def test_auto_generated_ids_and_utc(self) -> None:
        req = AuditRequest(account_id="synthetic-001", session_id="sess-1")
        assert req.request_id  # auto UUID
        assert req.requested_at.tzinfo is not None  # UTC-aware