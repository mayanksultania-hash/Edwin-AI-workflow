"""Validate and normalize workflow plans."""

from ai_workflow.models.orchestration import PlanStep, WorkflowPlan
from ai_workflow.models.tool_manifest import ToolManifest


class WorkflowPlanValidationError(ValueError):
    """Raised when an AI-created plan uses invalid tools or actions."""


def normalize_and_validate_plan(
    plan: WorkflowPlan,
    tool_manifest: ToolManifest,
) -> WorkflowPlan:
    allowed_actions = set(tool_manifest.action_names())
    normalized_steps = tuple(
        _normalize_step(step=step, allowed_actions=allowed_actions)
        for step in plan.steps
    )
    return WorkflowPlan(intent=plan.intent, steps=normalized_steps)


def _normalize_step(step: PlanStep, allowed_actions: set[str]) -> PlanStep:
    tool = step.tool
    action = step.action

    full_action = _find_allowed_action(tool=tool, action=action, allowed_actions=allowed_actions)
    if full_action:
        tool, action = full_action.rsplit(".", 1)

    if not full_action:
        raise WorkflowPlanValidationError(
            f"Plan step '{step.goal}' uses unsupported action '{tool}.{action}'"
        )

    return PlanStep(
        order=step.order,
        goal=step.goal,
        tool=tool,
        action=action,
        inputs=step.inputs,
    )


def _find_allowed_action(
    tool: str,
    action: str,
    allowed_actions: set[str],
) -> str | None:
    candidates = (
        f"{tool}.{action}",
        tool,
        action,
    )

    for candidate in candidates:
        if candidate in allowed_actions:
            return candidate

    if "." in tool:
        possible_tool, possible_action = tool.rsplit(".", 1)
        if possible_action == action and f"{possible_tool}.{action}" in allowed_actions:
            return f"{possible_tool}.{action}"

    if "." in action:
        possible_tool, possible_action = action.rsplit(".", 1)
        if possible_tool == tool and action in allowed_actions:
            return action

    return None
