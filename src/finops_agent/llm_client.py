"""LLM client for generating cost optimization recommendations.

This is the ONLY place the LLM is invoked in v1 (design Section 2).
The deterministic layer finds facts; this layer reasons about them.

Design reference:
- design.md Section 4.6 (Recommendation Engine)
- design.md Section 11.10 (cost: use cheaper model)
"""
from __future__ import annotations

import json
import os
from decimal import Decimal

from dotenv import load_dotenv
from openai import AzureOpenAI

from finops_agent.models import (
    Recommendation,
    RecommendationAction,
    Resource,
    RiskLevel,
)

load_dotenv()


class LLMConfigError(Exception):
    """Raised when required LLM configuration is missing."""


def _get_client() -> AzureOpenAI:
    """Build the Azure OpenAI client from environment config."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    if not endpoint or not api_key:
        raise LLMConfigError(
            "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in environment."
        )

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )


def _build_prompt(idle_resources: list[Resource]) -> str:
    """Build the prompt describing idle resources for the LLM."""
    lines = ["The following AWS EC2 instances are idle (low CPU usage):", ""]
    for r in idle_resources:
        cpu = r.utilization_metrics.get("cpu_avg_14d", "unknown")
        lines.append(
            f"- Resource ID: {r.resource_id}, "
            f"Type: {r.resource_type.value}, "
            f"Monthly cost: ${r.monthly_cost}, "
            f"Avg CPU (14d): {cpu}%"
        )
    lines.append("")
    lines.append(
        "For EACH instance, produce a recommendation as a JSON array. "
        "Each item must have exactly these fields:\n"
        '  "resource_id": the instance id,\n'
        '  "action": one of ["stop", "resize", "review"],\n'
        '  "estimated_savings": a number (the monthly cost saved),\n'
        '  "risk_level": one of ["low", "medium", "high"],\n'
        '  "rationale": a one-sentence reason.\n'
        "Return ONLY the JSON array, no other text."
    )
    return "\n".join(lines)


def generate_recommendations(idle_resources: list[Resource]) -> list[Recommendation]:
    """Generate optimization recommendations for idle resources.

    Args:
        idle_resources: List of idle EC2 Resource objects.

    Returns:
        List of Recommendation objects (validation_status defaults to PENDING).
        Returns empty list if no idle resources provided.
    """
    if not idle_resources:
        return []

    client = _get_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
    prompt = _build_prompt(idle_resources)

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a FinOps cost optimization assistant. "
                    "You return only valid JSON, never prose."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,  # low temp = consistent, less creative
    )

    raw = response.choices[0].message.content or "[]"
    return _parse_recommendations(raw)


def _parse_recommendations(raw: str) -> list[Recommendation]:
    """Parse the LLM's JSON response into Recommendation models."""
    # Strip common markdown fences if the model added them
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    items = json.loads(cleaned)

    recommendations: list[Recommendation] = []
    for idx, item in enumerate(items, start=1):
        recommendations.append(
            Recommendation(
                finding_id=item["resource_id"],  # link to the resource
                action=RecommendationAction(item["action"]),
                rationale=item["rationale"],
                estimated_savings=Decimal(str(item["estimated_savings"])),
                risk_level=RiskLevel(item["risk_level"]),
                priority=idx,  # order = priority for v1
            )
        )
    return recommendations