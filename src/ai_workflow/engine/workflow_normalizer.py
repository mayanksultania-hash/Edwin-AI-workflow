"""Normalize AI-created workflows before validation and code generation."""

from typing import Any

from ai_workflow.models.orchestration import Intent
from ai_workflow.models.workflow import Step, Workflow
from ai_workflow.orchestration.context_requirements import ENTITY_ALIASES


NORMALIZED_CONTEXT_KEYS = {
    "user",
    "system",
    "resource",
    "event_type",
    "severity",
    "source",
    "alert_type",
    "incident_type",
}


def normalize_workflow_inputs(workflow: Workflow, intent: Intent) -> Workflow:
    literal_to_reference = _literal_to_reference_map(intent)
    if not literal_to_reference:
        return workflow

    normalized_steps = tuple(
        Step(
            id=step.id,
            tool=step.tool,
            action=step.action,
            inputs=_normalize_value(step.inputs, literal_to_reference),
        )
        for step in workflow.steps
    )
    return Workflow(
        name=workflow.name,
        version=workflow.version,
        trigger=workflow.trigger,
        steps=normalized_steps,
    )


def _literal_to_reference_map(intent: Intent) -> dict[str, str]:
    mapping: dict[str, str] = {}

    for key, value in intent.entities.items():
        if not isinstance(value, str) or not value:
            continue

        context_key = ENTITY_ALIASES.get(key, key)
        if context_key in NORMALIZED_CONTEXT_KEYS:
            mapping[value] = f"$context.{context_key}"

    return mapping


def _normalize_value(value: Any, literal_to_reference: dict[str, str]) -> Any:
    if isinstance(value, str):
        if value.startswith("$"):
            return value
        return literal_to_reference.get(value, value)

    if isinstance(value, dict):
        return {
            key: _normalize_value(nested_value, literal_to_reference)
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [
            _normalize_value(nested_value, literal_to_reference)
            for nested_value in value
        ]

    return value
