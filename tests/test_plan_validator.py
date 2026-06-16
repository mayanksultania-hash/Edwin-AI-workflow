from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.orchestration import Intent, PlanStep, WorkflowPlan
from ai_workflow.orchestration.plan_validator import (
    WorkflowPlanValidationError,
    normalize_and_validate_plan,
)
from ai_workflow.tools.tool_manifest import build_default_tool_manifest


def test_normalize_and_validate_plan_accepts_valid_tool_action():
    plan = WorkflowPlan(
        intent=Intent(name="access_request", domain="identity_access", summary="access"),
        steps=(
            PlanStep(
                order=1,
                goal="Request access",
                tool="access_tool",
                action="request_access",
            ),
        ),
    )

    normalized = normalize_and_validate_plan(
        plan=plan,
        tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
    )

    assert normalized.steps[0].tool == "access_tool"


def test_normalize_and_validate_plan_fixes_tool_with_action_suffix():
    plan = WorkflowPlan(
        intent=Intent(name="access_request", domain="identity_access", summary="access"),
        steps=(
            PlanStep(
                order=1,
                goal="Request access",
                tool="access_tool.request_access",
                action="request_access",
            ),
        ),
    )

    normalized = normalize_and_validate_plan(
        plan=plan,
        tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
    )

    assert normalized.steps[0].tool == "access_tool"
    assert normalized.summary_lines()[0] == (
        "1. Request access using access_tool.request_access"
    )


def test_normalize_and_validate_plan_fixes_full_action_in_both_fields():
    plan = WorkflowPlan(
        intent=Intent(name="access_request", domain="identity_access", summary="access"),
        steps=(
            PlanStep(
                order=1,
                goal="Request access",
                tool="access_tool.request_access",
                action="access_tool.request_access",
            ),
        ),
    )

    normalized = normalize_and_validate_plan(
        plan=plan,
        tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
    )

    assert normalized.steps[0].tool == "access_tool"
    assert normalized.steps[0].action == "request_access"


def test_normalize_and_validate_plan_fixes_full_action_in_action_field():
    plan = WorkflowPlan(
        intent=Intent(name="access_request", domain="identity_access", summary="access"),
        steps=(
            PlanStep(
                order=1,
                goal="Request access",
                tool="access_tool",
                action="access_tool.request_access",
            ),
        ),
    )

    normalized = normalize_and_validate_plan(
        plan=plan,
        tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
    )

    assert normalized.steps[0].tool == "access_tool"
    assert normalized.steps[0].action == "request_access"


def test_normalize_and_validate_plan_rejects_unknown_action():
    plan = WorkflowPlan(
        intent=Intent(name="access_request", domain="identity_access", summary="access"),
        steps=(
            PlanStep(
                order=1,
                goal="Bad step",
                tool="missing_tool",
                action="run",
            ),
        ),
    )

    with pytest.raises(WorkflowPlanValidationError, match="unsupported action"):
        normalize_and_validate_plan(
            plan=plan,
            tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
        )
