"""Resolve inputs for workflow steps."""

from typing import Any

from ai_workflow.models.workflow import Step


class InputResolutionError(ValueError):
    """Raised when a step input reference cannot be resolved."""


def resolve_step_inputs(
    step: Step,
    previous_data: dict[str, Any],
    step_outputs: dict[str, dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        **previous_data,
        **_resolve_values(step.inputs, step_outputs, context),
    }


def _resolve_values(
    values: dict[str, Any],
    step_outputs: dict[str, dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in values.items():
        resolved[key] = _resolve_value(value, step_outputs, context)
    return resolved


def _resolve_value(
    value: Any,
    step_outputs: dict[str, dict[str, Any]],
    context: dict[str, Any],
) -> Any:
    if isinstance(value, str) and value.startswith("$steps."):
        return _resolve_path(value, "$steps.", step_outputs)

    if isinstance(value, str) and value.startswith("$context."):
        return _resolve_path(value, "$context.", context)

    if isinstance(value, dict):
        return _resolve_values(value, step_outputs, context)

    return value


def _resolve_path(reference: str, prefix: str, source: dict[str, Any]) -> Any:
    path = reference.removeprefix(prefix).split(".")
    current: Any = source

    for part in path:
        if not isinstance(current, dict) or part not in current:
            raise InputResolutionError(f"Cannot resolve input reference: {reference}")
        current = current[part]

    return current
