from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.workflow_yaml import (
    dump_workflow_yaml,
    load_workflow_yaml,
    load_workflow_yaml_file,
    write_workflow_yaml_file,
)
from ai_workflow.models.workflow import Workflow


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
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
"""


def test_load_workflow_yaml_builds_workflow_model():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    assert workflow.name == "critical_router_event_workflow"
    assert workflow.version == "v0.1"
    assert workflow.trigger.type == "natural_language"
    assert workflow.steps[0].id == "check_event"
    assert workflow.steps[0].inputs == {"severity": "critical"}


def test_dump_workflow_yaml_writes_readable_yaml():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    yaml_text = dump_workflow_yaml(workflow)

    assert "workflow:" in yaml_text
    assert "name: critical_router_event_workflow" in yaml_text
    assert "tool: event_tool" in yaml_text
    assert "severity: critical" in yaml_text


def test_dumped_yaml_can_be_loaded_again():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    loaded_again = load_workflow_yaml(dump_workflow_yaml(workflow))

    assert loaded_again == workflow


def test_workflow_yaml_file_round_trip(tmp_path):
    workflow = load_workflow_yaml(WORKFLOW_YAML)
    path = tmp_path / "workflow.yaml"

    write_workflow_yaml_file(workflow, path)
    loaded = load_workflow_yaml_file(path)

    assert loaded == workflow


def test_dump_workflow_yaml_accepts_model_created_from_dict():
    workflow = Workflow.from_dict(
        {
            "workflow": {
                "name": "access_request_workflow",
                "version": "v0.1",
                "trigger": {
                    "type": "natural_language",
                    "description": "give user access",
                },
                "steps": [
                    {
                        "id": "request_access",
                        "tool": "access_tool",
                        "action": "request_access",
                    }
                ],
            }
        }
    )

    yaml_text = dump_workflow_yaml(workflow)

    assert "name: access_request_workflow" in yaml_text
    assert "action: request_access" in yaml_text
