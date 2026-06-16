from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.workflow_normalizer import normalize_workflow_inputs
from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.models.orchestration import Intent


def test_normalize_workflow_inputs_replaces_matching_entities_with_context_refs():
    workflow = load_workflow_yaml(
        """
workflow:
  name: access_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: access
  steps:
    - id: request_access
      tool: access_tool
      action: request_access
      inputs:
        user: John
        system: Tableau
"""
    )
    intent = Intent(
        name="access_request",
        domain="access_management",
        summary="access",
        entities={"user": "John", "software": "Tableau"},
    )

    normalized = normalize_workflow_inputs(workflow=workflow, intent=intent)

    assert normalized.steps[0].inputs == {
        "user": "$context.user",
        "system": "$context.system",
    }


def test_normalize_workflow_inputs_keeps_non_entity_literals():
    workflow = load_workflow_yaml(
        """
workflow:
  name: event_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: event
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
      inputs:
        severity: critical
"""
    )
    intent = Intent(
        name="general_workflow",
        domain="automation",
        summary="event",
        entities={},
    )

    normalized = normalize_workflow_inputs(workflow=workflow, intent=intent)

    assert normalized.steps[0].inputs == {"severity": "critical"}


def test_normalize_workflow_inputs_replaces_event_entities_with_context_refs():
    workflow = load_workflow_yaml(
        """
workflow:
  name: event_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: event
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
      inputs:
        event_type: critical router event
        severity: critical
        source: router
"""
    )
    intent = Intent(
        name="incident_workflow",
        domain="incident_management",
        summary="event",
        entities={
            "event_type": "critical router event",
            "severity": "critical",
            "source": "router",
        },
    )

    normalized = normalize_workflow_inputs(workflow=workflow, intent=intent)

    assert normalized.steps[0].inputs == {
        "event_type": "$context.event_type",
        "severity": "$context.severity",
        "source": "$context.source",
    }


def test_normalize_workflow_inputs_keeps_existing_references():
    workflow = load_workflow_yaml(
        """
workflow:
  name: access_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: access
  steps:
    - id: request_access
      tool: access_tool
      action: request_access
      inputs:
        user: $context.user
        system: Tableau
"""
    )
    intent = Intent(
        name="access_request",
        domain="access_management",
        summary="access",
        entities={"user": "John", "system": "Tableau"},
    )

    normalized = normalize_workflow_inputs(workflow=workflow, intent=intent)

    assert normalized.steps[0].inputs == {
        "user": "$context.user",
        "system": "$context.system",
    }
