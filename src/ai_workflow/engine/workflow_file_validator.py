"""Validate saved workflow YAML files."""

from pathlib import Path

from ai_workflow.config.loader import load_config
from ai_workflow.engine.validator import WorkflowValidator
from ai_workflow.engine.workflow_yaml import load_workflow_yaml_file
from ai_workflow.models.validation import WorkflowFileValidationResult
from ai_workflow.tools.default_registry import build_default_registry


def validate_workflow_yaml_file(
    workflow_path: Path,
    config_path: Path | None = None,
    version_path: Path | None = None,
) -> WorkflowFileValidationResult:
    config = _load_config(config_path=config_path, version_path=version_path)
    registry = build_default_registry(enabled_tools=config.enabled_tools)
    workflow = load_workflow_yaml_file(workflow_path)

    WorkflowValidator(registry=registry).validate(workflow)

    return WorkflowFileValidationResult(path=workflow_path, workflow=workflow)


def _load_config(config_path: Path | None, version_path: Path | None):
    if config_path and version_path:
        return load_config(config_path=config_path, version_path=version_path)

    if config_path:
        return load_config(config_path=config_path)

    return load_config()
