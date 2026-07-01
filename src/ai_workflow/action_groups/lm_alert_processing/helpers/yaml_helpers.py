"""Shared YAML action-group lookup helpers."""

from typing import Any

from ai_workflow.action_groups.lm_alert_processing.config.constants import (
    MIN_ACTION_GROUP_STEPS,
)


def get_action_group(data: dict[str, Any]) -> dict[str, Any]:
    action_group = data.get("action_group")
    if not isinstance(action_group, dict):
        raise ValueError("YAML must contain action_group")
    return action_group


def find_step(action_group: dict[str, Any], step_name: str) -> dict[str, Any]:
    actions = action_group.get("actions", [])
    for step in actions:
        if isinstance(step, dict) and step.get("name") == step_name:
            return step
    raise ValueError(f"Step not found: {step_name}")


def remove_step(action_group: dict[str, Any], step_name: str) -> None:
    actions = action_group.get("actions")
    if not isinstance(actions, list):
        raise ValueError("action_group.actions must be a list")

    if len(actions) <= MIN_ACTION_GROUP_STEPS:
        raise ValueError("Cannot remove the last workflow step")

    for index, step in enumerate(actions):
        if isinstance(step, dict) and step.get("name") == step_name:
            del actions[index]
            return

    raise ValueError(f"Step not found: {step_name}")
