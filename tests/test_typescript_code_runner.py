from pathlib import Path
import asyncio
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.typescript_code_runner import (
    _build_node_runner,
    _transpile_typescript_to_javascript,
    run_generated_typescript_code,
)
from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.generator.code_templates import render_typescript_workflow
from ai_workflow.tools.default_registry import build_default_registry


def test_transpile_typescript_to_javascript_removes_export_and_types():
    javascript = _transpile_typescript_to_javascript(
        """
export const workflowName = "sample";
export const lastStepExecutions: Array<Record<string, any>> = [];
export async function main(
  context: Record<string, any>,
  tools: Record<string, any>,
): Promise<Record<string, any>> {
  return {};
}
"""
    )

    assert "export" not in javascript
    assert ": Record<string, any>" not in javascript
    assert ": Promise" not in javascript
    assert 'const workflowName = "sample";' in javascript
    assert "async function main(" in javascript


def test_build_node_runner_includes_context_and_mock_tools():
    runner = _build_node_runner(
        typescript_code='export const workflowName = "sample";',
        context={"user": "John"},
        tool_names=("access_tool",),
    )

    assert 'const context = {"user": "John"};' in runner
    assert 'const tools = createMockTools(["access_tool"]);' in runner
    assert "function createMockTools" in runner


def test_run_generated_typescript_code_reports_missing_node(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_workflow.engine.typescript_code_runner.shutil.which", lambda name: None)
    code_path = tmp_path / "sample.ts"
    code_path.write_text('export const workflowName = "sample";', encoding="utf-8")

    execution = asyncio.run(
        run_generated_typescript_code(
            code_path=code_path,
            registry=build_default_registry(enabled_tools=("access_tool",)),
            context={},
        )
    )

    assert execution.success is False
    assert "Node.js is required" in execution.error


def test_run_generated_typescript_code_executes_integration_style_code(tmp_path):
    if shutil.which("node") is None:
        return

    workflow = load_workflow_yaml(
        """
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
        user: $context.user
        system: $context.system
    - id: grant_tableau_access
      tool: access_tool
      action: grant_access
      inputs:
        request: $steps.request_tableau_access.request
"""
    )
    code_path = tmp_path / "give_tableau_access.ts"
    code_path.write_text(render_typescript_workflow(workflow), encoding="utf-8")

    execution = asyncio.run(
        run_generated_typescript_code(
            code_path=code_path,
            registry=build_default_registry(enabled_tools=("access_tool",)),
            context={"user": "John", "system": "Tableau"},
        )
    )

    assert execution.success is True
    assert execution.final_data == {
        "access_grant": {
            "request_id": "mock-access",
            "user": "John",
            "system": "Tableau",
            "status": "granted",
        }
    }
