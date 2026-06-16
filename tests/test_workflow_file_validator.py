from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.validator import WorkflowToolValidationError
from ai_workflow.engine.workflow_file_validator import validate_workflow_yaml_file


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_workflow_yaml_file_returns_result(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
generation:
  output_language: python
execution:
  mode: mock
tools:
  enabled:
    - event_tool
""",
    )
    workflow_path = write_file(
        tmp_path / "workflow.yaml",
        """
workflow:
  name: event_only_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: event only
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
""",
    )

    result = validate_workflow_yaml_file(
        workflow_path=workflow_path,
        config_path=config_path,
    )

    assert result.path == workflow_path
    assert result.workflow.name == "event_only_workflow"
    assert result.step_count == 1


def test_validate_workflow_yaml_file_rejects_disabled_tool(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
generation:
  output_language: python
execution:
  mode: mock
tools:
  enabled:
    - event_tool
""",
    )
    workflow_path = write_file(
        tmp_path / "workflow.yaml",
        """
workflow:
  name: incident_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: incident
  steps:
    - id: notify_servicenow
      tool: servicenow_tool
      action: create_incident
""",
    )

    with pytest.raises(WorkflowToolValidationError, match="unknown tool"):
        validate_workflow_yaml_file(
            workflow_path=workflow_path,
            config_path=config_path,
        )
