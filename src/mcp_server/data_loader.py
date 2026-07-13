"""Account data loader.

In v1, this reads from synthetic JSON fixtures.
In M2, this will be replaced with real AWS API calls (AssumeRole).
The tool functions depend on THIS contract, not on the data source,
so swapping to real AWS later requires no changes to the tools.

Design reference: design.md Section 10.3 (decoupling boundary)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from finops_agent.models import Resource

# For v1: fixtures live in tests/fixtures.
# Overridable via env var so we are not hard-coupled to the test folder.
_DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


class AccountNotFoundError(Exception):
    """Raised when no data exists for the requested account_id."""


def _fixture_path(account_id: str) -> Path:
    fixture_dir = Path(os.getenv("FINOPS_FIXTURE_DIR", str(_DEFAULT_FIXTURE_DIR)))
    return fixture_dir / f"{account_id}.json"


def load_account_resources(account_id: str) -> list:
    """Load all resources for an account as validated Resource models.

    v1: reads from synthetic fixture <account_id>.json
    M2: will be swapped for AWS AssumeRole + API calls.

    Raises:
        AccountNotFoundError: if no data file exists for the account.
    """
    # Map the friendly demo id to the fixture filename if needed
    fixture_file = _fixture_path(account_id)

    # Also support the "synthetic-001" -> "synthetic_account_001.json" alias
    if not fixture_file.exists() and account_id == "synthetic-001":
        fixture_file = _fixture_path("synthetic_account_001")

    if not fixture_file.exists():
        raise AccountNotFoundError(f"No data found for account_id={account_id!r}")

    with fixture_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [Resource.model_validate(r) for r in data.get("resources", [])]