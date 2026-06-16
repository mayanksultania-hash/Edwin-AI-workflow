"""Parse and validate orchestration agent outputs."""

import json
from typing import Any

from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    PlanStep,
    WorkflowPlan,
)


class OrchestrationParseError(ValueError):
    """Raised when orchestration output cannot be parsed."""


def parse_intent_json(text: str) -> Intent:
    data = _load_json_object(text)
    return Intent(
        name=_required_string(data, "name"),
        domain=_required_string(data, "domain"),
        summary=_required_string(data, "summary"),
        entities=_optional_dict(data.get("entities")),
    )


def parse_plan_json(text: str, intent: Intent) -> WorkflowPlan:
    data = _load_json_object(text)
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise OrchestrationParseError("plan requires at least one step")

    steps = tuple(_parse_plan_step(index, raw_step) for index, raw_step in enumerate(raw_steps))
    return WorkflowPlan(intent=intent, steps=steps)


def parse_code_verification_json(text: str) -> CodeVerification:
    data = _load_json_object(text)
    raw_issues = data.get("issues", [])
    if not isinstance(raw_issues, list):
        raise OrchestrationParseError("verification issues must be a list")

    issues = tuple(_issue_to_string(issue) for issue in raw_issues)
    risk_level = _required_string(data, "risk_level").lower()
    if risk_level not in {"low", "medium", "high"}:
        raise OrchestrationParseError("verification risk_level must be low, medium, or high")

    return CodeVerification(
        approved=_required_bool(data, "approved"),
        risk_level=risk_level,
        summary=_required_string(data, "summary"),
        issues=issues,
    )


def _parse_plan_step(index: int, data: Any) -> PlanStep:
    if not isinstance(data, dict):
        raise OrchestrationParseError(f"plan step {index + 1} must be an object")

    return PlanStep(
        order=_required_int(data, "order"),
        goal=_required_string(data, "goal"),
        tool=_required_string(data, "tool"),
        action=_required_string(data, "action"),
        inputs=_optional_dict(data.get("inputs")),
    )


def _load_json_object(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise OrchestrationParseError("orchestration output must be valid JSON") from error

    if not isinstance(data, dict):
        raise OrchestrationParseError("orchestration output must be a JSON object")

    return data


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OrchestrationParseError(f"missing required string: {key}")

    return value.strip()


def _required_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise OrchestrationParseError(f"missing required integer: {key}")

    return value


def _required_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise OrchestrationParseError(f"missing required boolean: {key}")

    return value


def _optional_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise OrchestrationParseError("expected object value")

    return value


def _issue_to_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)
