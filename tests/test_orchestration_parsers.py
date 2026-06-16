from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.orchestration import Intent
from ai_workflow.orchestration.parsers import (
    OrchestrationParseError,
    parse_code_verification_json,
    parse_intent_json,
    parse_plan_json,
)


def test_parse_intent_json_returns_intent():
    intent = parse_intent_json(
        """
{
  "name": "access_request",
  "domain": "identity_access",
  "summary": "Create an access workflow",
  "entities": {"user": "John", "system": "Tableau"}
}
"""
    )

    assert intent.name == "access_request"
    assert intent.domain == "identity_access"
    assert intent.entities == {"user": "John", "system": "Tableau"}


def test_parse_plan_json_returns_plan():
    intent = Intent(name="access_request", domain="identity_access", summary="summary")

    plan = parse_plan_json(
        """
{
  "steps": [
    {
      "order": 1,
      "goal": "Request access",
      "tool": "access_tool",
      "action": "request_access",
      "inputs": {"user": "John", "system": "Tableau"}
    }
  ]
}
""",
        intent=intent,
    )

    assert plan.intent == intent
    assert plan.steps[0].tool == "access_tool"
    assert plan.steps[0].inputs == {"user": "John", "system": "Tableau"}


def test_parse_code_verification_json_returns_result():
    result = parse_code_verification_json(
        """
{
  "approved": true,
  "risk_level": "low",
  "summary": "Generated code matches the workflow.",
  "issues": []
}
"""
    )

    assert result.approved is True
    assert result.risk_level == "low"
    assert result.summary == "Generated code matches the workflow."
    assert result.issues == ()


def test_parse_intent_json_rejects_invalid_json():
    with pytest.raises(OrchestrationParseError):
        parse_intent_json("not json")
