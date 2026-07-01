"""Read and write workflow YAML."""

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

from ai_workflow.models.workflow import Workflow


def load_workflow_yaml(yaml_text: str) -> Workflow:
    data = _parse_yaml(yaml_text)
    return Workflow.from_dict(data)


def load_workflow_yaml_file(path: Path) -> Workflow:
    return load_workflow_yaml(path.read_text(encoding="utf-8"))


def dump_workflow_yaml(workflow: Workflow) -> str:
    data = workflow.to_dict()
    if yaml:
        return yaml.safe_dump(data, sort_keys=False)

    return _dump_simple_workflow(data)


def write_workflow_yaml_file(workflow: Workflow, path: Path) -> None:
    path.write_text(dump_workflow_yaml(workflow), encoding="utf-8")


def _parse_yaml(yaml_text: str) -> dict[str, Any]:
    if yaml:
        data = yaml.safe_load(yaml_text) or {}
        return _normalize_workflow_yaml_data(data)

    return _parse_simple_workflow_yaml(yaml_text)


def _normalize_workflow_yaml_data(data: dict[str, Any]) -> dict[str, Any]:
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        return data

    trigger = workflow.get("trigger")
    if (
        "steps" not in workflow
        and isinstance(trigger, dict)
        and isinstance(trigger.get("steps"), list)
    ):
        workflow["steps"] = trigger.pop("steps")

    return data


def _parse_simple_workflow_yaml(yaml_text: str) -> dict[str, Any]:
    workflow: dict[str, Any] = {}
    trigger: dict[str, str] = {}
    steps: list[dict[str, Any]] = []
    current_step: dict[str, Any] | None = None
    current_inputs: dict[str, str] | None = None

    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if not stripped or stripped.startswith("#") or stripped == "workflow:":
            continue

        if indent == 2:
            key, value = _split_key_value(stripped)
            if key == "trigger":
                current_step = None
                continue
            if key == "steps":
                current_step = None
                continue
            workflow[key] = value
            current_inputs = None
            continue

        if indent == 4:
            if stripped.startswith("- "):
                current_step = {}
                steps.append(current_step)
                key, value = _split_key_value(stripped[2:])
                current_step[key] = value
                current_inputs = None
                continue

            key, value = _split_key_value(stripped)
            if key == "inputs":
                current_inputs = {}
                if current_step is not None:
                    current_step["inputs"] = current_inputs
                continue

            if current_step is not None:
                current_step[key] = value
            else:
                trigger[key] = value
            continue

        if indent == 6 and current_step is not None:
            key, value = _split_key_value(stripped)
            if key == "inputs":
                current_inputs = {}
                current_step["inputs"] = current_inputs
                continue

            current_step[key] = value
            continue

        if indent == 8 and current_inputs is not None:
            key, value = _split_key_value(stripped)
            current_inputs[key] = value

    workflow["trigger"] = trigger
    workflow["steps"] = steps
    return {"workflow": workflow}


def _dump_simple_workflow(data: dict[str, Any]) -> str:
    workflow = data["workflow"]
    lines = [
        "workflow:",
        f"  name: {workflow['name']}",
        f"  version: {workflow['version']}",
        "  trigger:",
        f"    type: {workflow['trigger']['type']}",
        f"    description: {workflow['trigger']['description']}",
        "  steps:",
    ]

    for step in workflow["steps"]:
        lines.append(f"    - id: {step['id']}")
        lines.append(f"      tool: {step['tool']}")
        lines.append(f"      action: {step['action']}")
        if step.get("inputs"):
            lines.append("      inputs:")
            for key, value in step["inputs"].items():
                lines.append(f"        {key}: {value}")

    return "\n".join(lines) + "\n"


def _split_key_value(text: str) -> tuple[str, str]:
    key, value = text.split(":", 1)
    return key.strip(), value.strip()
