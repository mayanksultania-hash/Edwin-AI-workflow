from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.generator.code_generator import generate_workflow_code


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
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
    - id: notify_servicenow
      tool: servicenow_tool
      action: create_incident
"""


def test_generate_python_workflow_code():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    code = generate_workflow_code(workflow, language="python")

    assert "WORKFLOW_NAME = 'critical_router_event_workflow'" in code
    assert "async def main(context: dict[str, Any], tools: dict[str, Any])" in code
    assert "step_1_result = await event.match_event()" in code
    assert "step_2_result = await alert.create_or_update_alert()" in code
    assert "step_3_result = await servicenow.create_incident()" in code
    assert "return step_outputs['notify_servicenow']" in code


def test_generate_typescript_workflow_code():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    code = generate_workflow_code(workflow, language="typescript")

    assert 'export const workflowName = "critical_router_event_workflow";' in code
    assert "export async function main(" in code
    assert "const step1Result = await event.match_event(" in code
    assert "const step2Result = await alert.create_or_update_alert(" in code
    assert "const step3Result = await servicenow.create_incident(" in code
    assert "    {}," in code
    assert 'return stepOutputs["notify_servicenow"];' in code


def test_generate_code_rejects_unknown_language():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    with pytest.raises(ValueError, match="Unsupported code language"):
        generate_workflow_code(workflow, language="go")
