from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.workflow import Workflow, WorkflowValidationError


def valid_workflow_data():
    return {
        "workflow": {
            "name": "critical_router_event_workflow",
            "version": "v0.1",
            "trigger": {
                "type": "natural_language",
                "description": "critical router event more than 3 times",
            },
            "steps": [
                {
                    "id": "check_event",
                    "tool": "event_tool",
                    "action": "match_event",
                    "inputs": {"severity": "critical"},
                },
                {
                    "id": "create_alert",
                    "tool": "alert_tool",
                    "action": "create_or_update_alert",
                },
            ],
        }
    }


def test_workflow_from_dict_builds_model():
    workflow = Workflow.from_dict(valid_workflow_data())

    assert workflow.name == "critical_router_event_workflow"
    assert workflow.version == "v0.1"
    assert workflow.trigger.type == "natural_language"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].inputs == {"severity": "critical"}


def test_workflow_to_dict_round_trips_shape():
    workflow = Workflow.from_dict(valid_workflow_data())

    assert workflow.to_dict() == valid_workflow_data()


def test_workflow_accepts_unwrapped_data():
    data = valid_workflow_data()["workflow"]

    workflow = Workflow.from_dict(data)

    assert workflow.name == "critical_router_event_workflow"


def test_workflow_requires_name():
    data = valid_workflow_data()
    data["workflow"]["name"] = ""

    with pytest.raises(WorkflowValidationError, match="workflow requires"):
        Workflow.from_dict(data)


def test_workflow_requires_trigger_object():
    data = valid_workflow_data()
    data["workflow"]["trigger"] = None

    with pytest.raises(WorkflowValidationError, match="trigger must be an object"):
        Workflow.from_dict(data)


def test_workflow_requires_at_least_one_step():
    data = valid_workflow_data()
    data["workflow"]["steps"] = []

    with pytest.raises(WorkflowValidationError, match="at least one step"):
        Workflow.from_dict(data)


def test_workflow_rejects_step_without_action():
    data = valid_workflow_data()
    del data["workflow"]["steps"][0]["action"]

    with pytest.raises(WorkflowValidationError, match="requires non-empty string 'action'"):
        Workflow.from_dict(data)


def test_workflow_rejects_duplicate_step_ids():
    data = valid_workflow_data()
    data["workflow"]["steps"][1]["id"] = "check_event"

    with pytest.raises(WorkflowValidationError, match="duplicate step id"):
        Workflow.from_dict(data)


def test_workflow_rejects_non_object_inputs():
    data = valid_workflow_data()
    data["workflow"]["steps"][0]["inputs"] = "critical"

    with pytest.raises(WorkflowValidationError, match="inputs must be an object"):
        Workflow.from_dict(data)
