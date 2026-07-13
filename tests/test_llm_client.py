"""Tests for the LLM client.

Unit tests mock the LLM (fast, free, deterministic).
The integration test hits the real API and is skipped unless
RUN_LLM_INTEGRATION=1 is set.
"""
from __future__ import annotations

import os
from decimal import Decimal

import pytest

from finops_agent.llm_client import (
    _build_prompt,
    _parse_recommendations,
    generate_recommendations,
)
from finops_agent.models import (
    RecommendationAction,
    Resource,
    ResourceType,
    RiskLevel,
    ValidationStatus,
)


def _make_idle_resource(rid: str, cost: str, cpu: float) -> Resource:
    return Resource(
        resource_id=rid,
        resource_type=ResourceType.EC2,
        region="us-east-1",
        monthly_cost=Decimal(cost),
        utilization_metrics={"cpu_avg_14d": cpu},
    )


class TestBuildPrompt:
    def test_prompt_includes_resource_ids(self) -> None:
        resources = [_make_idle_resource("i-1", "50", 2.5)]
        prompt = _build_prompt(resources)
        assert "i-1" in prompt
        assert "50" in prompt

    def test_prompt_requests_json(self) -> None:
        prompt = _build_prompt([_make_idle_resource("i-1", "50", 2.5)])
        assert "JSON" in prompt


class TestParseRecommendations:
    def test_parses_plain_json(self) -> None:
        raw = (
            '[{"resource_id": "i-1", "action": "stop", '
            '"estimated_savings": 50, "risk_level": "low", '
            '"rationale": "Idle for 14 days"}]'
        )
        recs = _parse_recommendations(raw)
        assert len(recs) == 1
        assert recs[0].action == RecommendationAction.STOP
        assert recs[0].estimated_savings == Decimal("50")
        assert recs[0].risk_level == RiskLevel.LOW
        assert recs[0].validation_status == ValidationStatus.PENDING

    def test_parses_json_wrapped_in_markdown(self) -> None:
        raw = (
            "```json\n"
            '[{"resource_id": "i-2", "action": "review", '
            '"estimated_savings": 30, "risk_level": "medium", '
            '"rationale": "Low usage"}]\n'
            "```"
        )
        recs = _parse_recommendations(raw)
        assert len(recs) == 1
        assert recs[0].action == RecommendationAction.REVIEW

    def test_priority_assigned_by_order(self) -> None:
        raw = (
            '[{"resource_id": "i-1", "action": "stop", "estimated_savings": 50, '
            '"risk_level": "low", "rationale": "a"},'
            '{"resource_id": "i-2", "action": "stop", "estimated_savings": 30, '
            '"risk_level": "low", "rationale": "b"}]'
        )
        recs = _parse_recommendations(raw)
        assert recs[0].priority == 1
        assert recs[1].priority == 2

    def test_invalid_action_rejected(self) -> None:
        raw = (
            '[{"resource_id": "i-1", "action": "terminate", '
            '"estimated_savings": 50, "risk_level": "low", "rationale": "x"}]'
        )
        with pytest.raises(ValueError):
            _parse_recommendations(raw)


class TestGenerateRecommendations:
    def test_empty_input_returns_empty(self) -> None:
        assert generate_recommendations([]) == []


@pytest.mark.skipif(
    os.getenv("RUN_LLM_INTEGRATION") != "1",
    reason="Set RUN_LLM_INTEGRATION=1 to run real LLM calls",
)
class TestLLMIntegration:
    def test_real_llm_returns_recommendations(self) -> None:
        resources = [_make_idle_resource("i-fake-001", "50", 2.5)]
        recs = generate_recommendations(resources)
        assert len(recs) >= 1
        assert recs[0].finding_id == "i-fake-001"