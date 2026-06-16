from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.orchestration import Intent, MCPContext
from ai_workflow.orchestration.context_requirements import (
    MissingContextError,
    context_from_intent,
    validate_required_context,
)


def test_context_from_intent_maps_aliases_to_system():
    intent = Intent(
        name="access_request",
        domain="access_management",
        summary="access",
        entities={"user": "John", "resource": "Tableau"},
    )

    assert context_from_intent(intent) == {
        "user": "John",
        "resource": "Tableau",
        "system": "Tableau",
    }


def test_validate_required_context_accepts_available_context():
    intent = Intent(
        name="access_request",
        domain="access_management",
        summary="access",
        entities={"user": "John", "system": "Tableau"},
    )
    mcp_context = MCPContext(
        source="mock_mcp",
        values={"context_keys": ["user", "system"]},
    )

    validate_required_context(intent=intent, mcp_context=mcp_context)


def test_validate_required_context_raises_with_questions():
    intent = Intent(
        name="access_request",
        domain="access_management",
        summary="access",
        entities={"system": "Tableau"},
    )
    mcp_context = MCPContext(
        source="mock_mcp",
        values={"context_keys": ["user", "system"]},
    )

    with pytest.raises(MissingContextError) as error:
        validate_required_context(intent=intent, mcp_context=mcp_context)

    assert error.value.missing_keys == ("user",)
    assert error.value.questions == ("Who should this workflow run for?",)
