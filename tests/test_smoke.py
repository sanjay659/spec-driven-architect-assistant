"""Smoke test to verify pytest setup works."""


def test_imports():
    """Verify all core packages import cleanly."""
    import finops_agent
    import mcp_server
    import eval_harness

    assert finops_agent is not None
    assert mcp_server is not None
    assert eval_harness is not None


def test_python_version():
    """Verify we're running Python 3.12+."""
    import sys

    assert sys.version_info >= (3, 12), f"Expected Python 3.12+, got {sys.version_info}"
    assert sys.version_info < (3, 14), f"Expected Python < 3.14, got {sys.version_info}"


def test_pydantic_v2():
    """Verify pydantic v2 is installed (v1 has different API)."""
    import pydantic

    major_version = int(pydantic.VERSION.split(".")[0])
    assert major_version >= 2, f"Expected Pydantic v2+, got {pydantic.VERSION}"