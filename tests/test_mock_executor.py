from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.mock_executor import execute_mock_workflow
from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.tools.default_registry import build_default_registry


WORKFLOW_YAML = """
workflow:
  name: critical_router_event_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: critical router event more than 3 times
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
      inputs:
        severity: critical
        source: router
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
    - id: notify_servicenow
      tool: servicenow_tool
      action: create_incident
"""


def test_mock_executor_runs_workflow_steps_in_order():
    workflow = load_workflow_yaml(WORKFLOW_YAML)
    registry = build_default_registry()

    execution = asyncio.run(
        execute_mock_workflow(
            workflow=workflow,
            registry=registry,
            context={"request_id": "req-1"},
        )
    )

    assert execution.success is True
    assert execution.workflow_name == "critical_router_event_workflow"
    assert [step.step_id for step in execution.steps] == [
        "check_event",
        "create_alert",
        "notify_servicenow",
    ]
    assert execution.final_data["incident"]["number"] == "INC-REQ-1"
    assert execution.final_data["incident"]["severity"] == "critical"
    assert execution.final_data["incident"]["source"] == "router"


def test_mock_executor_stops_when_step_fails():
    workflow = load_workflow_yaml(
        """
workflow:
  name: failing_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: invalid action
  steps:
    - id: check_event
      tool: event_tool
      action: missing_action
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
"""
    )
    registry = build_default_registry()

    execution = asyncio.run(
        execute_mock_workflow(
            workflow=workflow,
            registry=registry,
            context={},
        )
    )

    assert execution.success is False
    assert len(execution.steps) == 1
    assert execution.steps[0].step_id == "check_event"
    assert "does not support action" in execution.error
