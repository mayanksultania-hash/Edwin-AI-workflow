from pathlib import Path
from types import SimpleNamespace
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.generator.code_templates import (
    python_literal,
    python_call_arguments,
    python_reference_expression,
    python_step_result_name,
    render_python_workflow,
    render_typescript_workflow,
    to_camel_case,
    typescript_literal,
    typescript_reference_expression,
    typescript_step_result_name,
)


WORKFLOW_YAML = """
workflow:
  name: critical_router_event_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: critical router event
    steps:
    - id: check_event
      tool: event_tool
      action: match_event
      inputs:
        severity: critical
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
      inputs:
        event: $steps.check_event.event
"""

ACCESS_WORKFLOW_YAML = """
workflow:
  name: give_tableau_access
  version: v0.1
  trigger:
    type: natural_language
    description: Give John Tableau access
  steps:
    - id: request_tableau_access
      tool: access_tool
      action: request_access
      inputs:
        user: John
        system: Tableau
    - id: grant_tableau_access
      tool: access_tool
      action: grant_access
      inputs:
        request: $steps.request_tableau_access.request
"""


def test_to_camel_case_converts_snake_case():
    assert to_camel_case("critical_router_event_workflow") == (
        "criticalRouterEventWorkflow"
    )


def test_step_result_names():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    assert python_step_result_name(workflow.steps[0]) == "check_event_result"
    assert typescript_step_result_name(workflow.steps[0]) == "checkEventResult"


def test_render_python_workflow():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    code = render_python_workflow(workflow)

    assert "WORKFLOW_NAME = 'critical_router_event_workflow'" in code
    assert "from ai_workflow.integrations import alert, event" in code
    assert "with bind_runtime(tools=tools, context=context):" in code
    assert "async def main(context: dict[str, Any], tools: dict[str, Any])" in code
    assert (
        "step_1_result = await event.match_event(severity='critical')"
    ) in code
    assert (
        "step_2_result = await alert.create_or_update_alert("
        "event=step_outputs['check_event']['event'])"
    ) in code
    assert "return step_outputs['create_alert']" in code


def test_render_typescript_workflow():
    workflow = load_workflow_yaml(WORKFLOW_YAML)

    code = render_typescript_workflow(workflow)

    assert 'export const workflowName = "critical_router_event_workflow";' in code
    assert "function createIntegration(" in code
    assert 'const event = createIntegration("event_tool", tools, context);' in code
    assert 'const alert = createIntegration("alert_tool", tools, context);' in code
    assert "export async function main(" in code
    assert "const step1Result = await event.match_event(" in code
    assert '    "severity": "critical",' in code
    assert (
        'const step2Result = await alert.create_or_update_alert('
    ) in code
    assert '    "event": stepOutputs["check_event"]["event"],' in code
    assert 'return stepOutputs["create_alert"];' in code


def test_render_python_workflow_resolves_step_references():
    workflow = load_workflow_yaml(ACCESS_WORKFLOW_YAML)

    code = render_python_workflow(workflow)

    assert (
        "step_2_result = await access.grant_access("
        "request=step_outputs['request_tableau_access']['request'])"
    ) in code


def test_render_typescript_workflow_resolves_step_references():
    workflow = load_workflow_yaml(ACCESS_WORKFLOW_YAML)

    code = render_typescript_workflow(workflow)

    assert (
        'const step2Result = await access.grant_access('
    ) in code
    assert '    "request": stepOutputs["request_tableau_access"]["request"],' in code


def test_render_python_workflow_is_executable_with_tools():
    workflow = load_workflow_yaml(ACCESS_WORKFLOW_YAML)
    namespace = {}
    exec(render_python_workflow(workflow), namespace)

    class FakeAccessTool:
        async def execute(self, action, inputs, context):
            if action == "request_access":
                return SimpleNamespace(
                    success=True,
                    error=None,
                    data={
                        "request": {
                            "id": "req-1",
                            "user": inputs["user"],
                            "system": inputs["system"],
                        }
                    },
                )

            return SimpleNamespace(
                success=True,
                error=None,
                data={
                    "access_grant": {
                        "request_id": inputs["request"]["id"],
                        "user": inputs["request"]["user"],
                        "system": inputs["request"]["system"],
                    }
                },
            )

    result = asyncio.run(
        namespace["main"](
            context={},
            tools={"access_tool": FakeAccessTool()},
        )
    )

    assert result == {
        "access_grant": {
            "request_id": "req-1",
            "user": "John",
            "system": "Tableau",
        }
    }


def test_literals_render_step_inputs():
    inputs = {"user": "John", "system": "Tableau"}

    assert python_literal(inputs) == "{'user': 'John', 'system': 'Tableau'}"
    assert typescript_literal(inputs) == '{"user": "John", "system": "Tableau"}'


def test_python_call_arguments_renders_keyword_inputs():
    inputs = {"user": "$context.user", "system": "$context.system"}

    assert python_call_arguments(inputs) == (
        "user=context['user'], system=context['system']"
    )


def test_reference_expressions_render_step_and_context_paths():
    assert python_reference_expression("$steps.request_access.request") == (
        "step_outputs['request_access']['request']"
    )
    assert python_reference_expression("$context.ticket.id") == "context['ticket']['id']"
    assert typescript_reference_expression("$steps.request_access.request") == (
        'stepOutputs["request_access"]["request"]'
    )
    assert typescript_reference_expression("$context.ticket.id") == (
        'context["ticket"]["id"]'
    )
