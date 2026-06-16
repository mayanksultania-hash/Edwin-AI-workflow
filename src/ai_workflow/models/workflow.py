"""Workflow models used by generators and executors."""

from dataclasses import dataclass, field
from typing import Any


class WorkflowValidationError(ValueError):
    """Raised when workflow data is not valid."""


@dataclass(frozen=True)
class Trigger:
    type: str
    description: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trigger":
        if not isinstance(data, dict):
            raise WorkflowValidationError("trigger must be an object")

        trigger_type = _required_string(data, "type", "trigger")
        description = _required_string(data, "description", "trigger")

        return cls(type=trigger_type, description=description)

    def to_dict(self) -> dict[str, str]:
        return {
            "type": self.type,
            "description": self.description,
        }


@dataclass(frozen=True)
class Step:
    id: str
    tool: str
    action: str
    inputs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        if not isinstance(data, dict):
            raise WorkflowValidationError("step must be an object")

        step_id = _required_string(data, "id", "step")
        tool = _required_string(data, "tool", f"step '{step_id}'")
        action = _required_string(data, "action", f"step '{step_id}'")
        inputs = data.get("inputs", {})

        if not isinstance(inputs, dict):
            raise WorkflowValidationError(f"step '{step_id}' inputs must be an object")

        return cls(id=step_id, tool=tool, action=action, inputs=inputs)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "tool": self.tool,
            "action": self.action,
        }

        if self.inputs:
            data["inputs"] = self.inputs

        return data


@dataclass(frozen=True)
class Workflow:
    name: str
    version: str
    trigger: Trigger
    steps: tuple[Step, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        if not isinstance(data, dict):
            raise WorkflowValidationError("workflow data must be an object")

        workflow_data = data.get("workflow", data)
        if not isinstance(workflow_data, dict):
            raise WorkflowValidationError("workflow must be an object")

        name = _required_string(workflow_data, "name", "workflow")
        version = _required_string(workflow_data, "version", "workflow")
        trigger = Trigger.from_dict(workflow_data.get("trigger"))
        steps = _load_steps(workflow_data.get("steps"))
        _ensure_unique_step_ids(steps)

        return cls(name=name, version=version, trigger=trigger, steps=tuple(steps))

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": {
                "name": self.name,
                "version": self.version,
                "trigger": self.trigger.to_dict(),
                "steps": [step.to_dict() for step in self.steps],
            }
        }


def _required_string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkflowValidationError(f"{label} requires non-empty string '{key}'")
    return value.strip()


def _load_steps(raw_steps: Any) -> list[Step]:
    if not isinstance(raw_steps, list) or not raw_steps:
        raise WorkflowValidationError("workflow requires at least one step")

    return [Step.from_dict(step) for step in raw_steps]


def _ensure_unique_step_ids(steps: list[Step]) -> None:
    seen: set[str] = set()
    for step in steps:
        if step.id in seen:
            raise WorkflowValidationError(f"duplicate step id: {step.id}")
        seen.add(step.id)
