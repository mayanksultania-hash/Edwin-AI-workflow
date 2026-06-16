from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.code_runner import run_generated_code
from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.generator.code_templates import render_python_workflow
from ai_workflow.tools.default_registry import build_default_registry


def test_run_generated_code_loads_and_executes_python_workflow(tmp_path):
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
        system: $context.system
    - id: grant_access
      tool: access_tool
      action: grant_access
      inputs:
        request: $steps.request_access.request
"""
    )
    code_path = tmp_path / "access_workflow.py"
    code_path.write_text(render_python_workflow(workflow), encoding="utf-8")

    execution = asyncio.run(
        run_generated_code(
            code_path=code_path,
            registry=build_default_registry(enabled_tools=("access_tool",)),
            context={"user": "John", "system": "Tableau"},
        )
    )

    assert execution.workflow_name == "access_workflow"
    assert execution.success is True
    assert [step.step_id for step in execution.steps] == [
        "request_access",
        "grant_access",
    ]
    assert execution.final_data["access_grant"]["user"] == "John"
    assert execution.final_data["access_grant"]["system"] == "Tableau"


def test_run_generated_code_returns_failed_execution_on_error(tmp_path):
    code_path = tmp_path / "broken_workflow.py"
    code_path.write_text(
        """
WORKFLOW_NAME = "broken_workflow"
LAST_STEP_EXECUTIONS = []

async def main(context, tools):
    raise RuntimeError("broken")
""",
        encoding="utf-8",
    )

    execution = asyncio.run(
        run_generated_code(
            code_path=code_path,
            registry=build_default_registry(enabled_tools=("access_tool",)),
            context={},
        )
    )

    assert execution.workflow_name == "broken_workflow"
    assert execution.success is False
    assert execution.error == "broken"
