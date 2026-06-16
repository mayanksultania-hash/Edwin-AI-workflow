from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.validator import (
    WorkflowToolValidationError,
    WorkflowValidator,
    validate_workflow_tools,
)
from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.tools.default_registry import build_default_registry


def test_validate_workflow_tools_accepts_registered_tools_and_actions():
    workflow = load_workflow_yaml(
        """
workflow:
  name: valid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: valid
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
"""
    )

    validate_workflow_tools(workflow, build_default_registry())


def test_workflow_validator_accepts_tools_and_references():
    workflow = load_workflow_yaml(
        """
workflow:
  name: valid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: valid
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
      inputs:
        event: $steps.check_event.event
"""
    )

    WorkflowValidator(registry=build_default_registry()).validate(workflow)


def test_validate_workflow_tools_rejects_unknown_tool():
    workflow = load_workflow_yaml(
        """
workflow:
  name: invalid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: invalid
  steps:
    - id: check_event
      tool: missing_tool
      action: match_event
"""
    )

    with pytest.raises(WorkflowToolValidationError, match="unknown tool"):
        validate_workflow_tools(workflow, build_default_registry())


def test_validate_workflow_tools_rejects_unsupported_action():
    workflow = load_workflow_yaml(
        """
workflow:
  name: invalid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: invalid
  steps:
    - id: check_event
      tool: event_tool
      action: create_event
"""
    )

    with pytest.raises(WorkflowToolValidationError, match="unsupported action"):
        validate_workflow_tools(workflow, build_default_registry())
