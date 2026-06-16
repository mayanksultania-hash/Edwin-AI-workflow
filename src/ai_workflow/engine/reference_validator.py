"""Validate workflow input references."""

from typing import Any

from ai_workflow.models.workflow import Workflow


class WorkflowReferenceValidationError(ValueError):
    """Raised when workflow input references are invalid."""


def validate_workflow_references(workflow: Workflow) -> None:
    available_steps: set[str] = set()

    for step in workflow.steps:
        for reference in _find_references(step.inputs):
            if reference.startswith("$steps."):
                step_id = _step_id_from_reference(reference)
                if step_id not in available_steps:
                    raise WorkflowReferenceValidationError(
                        f"Step '{step.id}' uses unavailable step reference '{reference}'"
                    )

        available_steps.add(step.id)


def _find_references(value: Any) -> list[str]:
    if isinstance(value, str) and value.startswith("$"):
        return [value]

    if isinstance(value, dict):
        references: list[str] = []
        for nested_value in value.values():
            references.extend(_find_references(nested_value))
        return references

    if isinstance(value, list):
        references: list[str] = []
        for nested_value in value:
            references.extend(_find_references(nested_value))
        return references

    return []


def _step_id_from_reference(reference: str) -> str:
    parts = reference.split(".")
    if len(parts) < 3 or parts[0] != "$steps":
        raise WorkflowReferenceValidationError(
            f"Invalid step reference format: {reference}"
        )
    return parts[1]
