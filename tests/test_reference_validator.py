from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.reference_validator import (
    WorkflowReferenceValidationError,
    validate_workflow_references,
)
from ai_workflow.engine.workflow_yaml import load_workflow_yaml


def test_validate_workflow_references_accepts_previous_step_reference():
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

    validate_workflow_references(workflow)


def test_validate_workflow_references_rejects_missing_step_reference():
    workflow = load_workflow_yaml(
        """
workflow:
  name: invalid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: invalid
  steps:
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
      inputs:
        event: $steps.check_event.event
"""
    )

    with pytest.raises(WorkflowReferenceValidationError, match="unavailable step"):
        validate_workflow_references(workflow)


def test_validate_workflow_references_rejects_future_step_reference():
    workflow = load_workflow_yaml(
        """
workflow:
  name: invalid_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: invalid
  steps:
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
      inputs:
        event: $steps.check_event.event
    - id: check_event
      tool: event_tool
      action: match_event
"""
    )

    with pytest.raises(WorkflowReferenceValidationError, match="unavailable step"):
        validate_workflow_references(workflow)


def test_validate_workflow_references_accepts_context_reference():
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
      inputs:
        request_id: $context.request_id
"""
    )

    validate_workflow_references(workflow)


def test_validate_workflow_references_checks_nested_values():
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
        payload:
          event: $steps.check_event.event
"""
    )

    validate_workflow_references(workflow)
