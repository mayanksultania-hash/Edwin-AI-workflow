"""Write generated workflow files."""

from pathlib import Path
import re
import json

from ai_workflow.engine.action_group_yaml import dump_action_group_yaml
from ai_workflow.models.action_group import ActionGroup
from ai_workflow.models.output import (
    ActionGroupOutputPaths,
    ActionServiceJsonOutputPaths,
    GeneratedOutputPaths,
)
from ai_workflow.models.run import WorkflowRunResult


def write_generated_outputs(
    result: WorkflowRunResult,
    output_dir: Path,
    language: str,
) -> GeneratedOutputPaths:
    workflow_dir = output_dir / "workflows"
    code_dir = output_dir / "code"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    code_dir.mkdir(parents=True, exist_ok=True)

    workflow_yaml_path = workflow_dir / f"{result.workflow.name}.yaml"
    generated_code_path = code_dir / f"{result.workflow.name}{_code_extension(language)}"

    workflow_yaml_path.write_text(result.workflow_yaml, encoding="utf-8")
    generated_code_path.write_text(result.generated_code, encoding="utf-8")

    return GeneratedOutputPaths(
        workflow_yaml_path=workflow_yaml_path,
        generated_code_path=generated_code_path,
    )


def write_action_group_output(
    action_group: ActionGroup,
    output_dir: Path,
) -> ActionGroupOutputPaths:
    action_group_dir = output_dir / "action_groups"
    action_group_dir.mkdir(parents=True, exist_ok=True)

    action_group_yaml_path = action_group_dir / f"{_slugify(action_group.name)}.yaml"
    action_group_yaml_path.write_text(
        dump_action_group_yaml(action_group),
        encoding="utf-8",
    )

    return ActionGroupOutputPaths(action_group_yaml_path=action_group_yaml_path)


def write_action_service_json_output(
    action_group_name: str,
    action_service_json: dict,
    output_dir: Path,
) -> ActionServiceJsonOutputPaths:
    action_service_dir = output_dir / "action_service_json"
    action_service_dir.mkdir(parents=True, exist_ok=True)

    action_service_json_path = action_service_dir / f"{_slugify(action_group_name)}.json"
    action_service_json_path.write_text(
        json.dumps(action_service_json, indent=2),
        encoding="utf-8",
    )

    return ActionServiceJsonOutputPaths(
        action_service_json_path=action_service_json_path,
    )


def _code_extension(language: str) -> str:
    if language == "python":
        return ".py"

    if language == "typescript":
        return ".ts"

    raise ValueError(f"Unsupported output language: {language}")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "action_group"
