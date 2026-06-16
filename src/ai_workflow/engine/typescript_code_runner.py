"""Run generated TypeScript workflow code with Node.js when available."""

import asyncio
import json
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from ai_workflow.models.execution import StepExecution, WorkflowExecution
from ai_workflow.tools.registry import ToolRegistry


def is_typescript_runtime_available() -> bool:
    return shutil.which("node") is not None


async def run_generated_typescript_code(
    code_path: Path,
    registry: ToolRegistry,
    context: dict[str, Any],
) -> WorkflowExecution:
    workflow_name = code_path.stem
    node_path = shutil.which("node")
    if not node_path:
        return WorkflowExecution(
            workflow_name=workflow_name,
            success=False,
            steps=(),
            error="Node.js is required to execute generated TypeScript code",
        )

    with TemporaryDirectory() as temp_dir:
        runner_path = Path(temp_dir) / "generated_workflow.mjs"
        runner_path.write_text(
            _build_node_runner(
                typescript_code=code_path.read_text(encoding="utf-8"),
                context=context,
                tool_names=registry.names(),
            ),
            encoding="utf-8",
        )
        process = await asyncio.create_subprocess_exec(
            node_path,
            str(runner_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return WorkflowExecution(
            workflow_name=workflow_name,
            success=False,
            steps=(),
            error=stderr.decode("utf-8").strip() or stdout.decode("utf-8").strip(),
        )

    data = json.loads(stdout.decode("utf-8"))
    return WorkflowExecution(
        workflow_name=data.get("workflowName", workflow_name),
        success=True,
        steps=_load_step_executions(data.get("lastStepExecutions", [])),
        final_data=data.get("finalData", {}),
    )


def _build_node_runner(
    typescript_code: str,
    context: dict[str, Any],
    tool_names: tuple[str, ...],
) -> str:
    return "\n".join(
        [
            _transpile_typescript_to_javascript(typescript_code),
            "",
            f"const context = {json.dumps(context)};",
            f"const tools = createMockTools({json.dumps(list(tool_names))});",
            "const finalData = await main(context, tools);",
            "console.log(JSON.stringify({ workflowName, lastStepExecutions, finalData }));",
            "",
            "function createMockTools(toolNames) {",
            "  const tools = {};",
            "  for (const name of toolNames) {",
            "    tools[name] = { execute: ({ action, inputs, context }) => executeMockTool(name, action, inputs, context) };",
            "  }",
            "  return tools;",
            "}",
            "",
            "async function executeMockTool(tool, action, inputs, context) {",
            "  if (tool === 'access_tool' && action === 'request_access') {",
            "    const request = { id: 'mock-access', user: inputs.user ?? 'unknown', system: inputs.system ?? inputs.resource ?? 'unknown', status: 'requested' };",
            "    return { success: true, error: null, data: { access_request: request, request } };",
            "  }",
            "  if (tool === 'access_tool' && action === 'grant_access') {",
            "    const request = inputs.request ?? {};",
            "    return { success: true, error: null, data: { access_grant: { request_id: request.id ?? 'unknown', user: request.user ?? 'unknown', system: request.system ?? 'unknown', status: 'granted' } } };",
            "  }",
            "  if (tool === 'event_tool' && action === 'match_event') {",
            "    return { success: true, error: null, data: { event: { severity: inputs.severity ?? 'critical', source: inputs.source ?? 'router' } } };",
            "  }",
            "  if (tool === 'alert_tool' && action === 'create_or_update_alert') {",
            "    return { success: true, error: null, data: { alert: { id: 'mock-alert', event: inputs.event ?? {} } } };",
            "  }",
            "  if (tool === 'servicenow_tool' && action === 'create_incident') {",
            "    return { success: true, error: null, data: { incident: { id: 'mock-incident', severity: 'critical', alert: inputs.alert ?? {} } } };",
            "  }",
            "  return { success: false, error: `Unsupported mock tool action: ${tool}.${action}`, data: {} };",
            "}",
        ]
    )


def _transpile_typescript_to_javascript(code: str) -> str:
    code = code.replace("export const ", "const ")
    code = code.replace("export async function ", "async function ")
    code = re.sub(r":\s*Array<Record<string,\s*any>>", "", code)
    code = re.sub(r":\s*Record<string,\s*any>", "", code)
    code = re.sub(r":\s*string", "", code)
    code = re.sub(r"\):\s*Promise<Record<string,\s*any>>\s*\{", ") {", code)
    code = re.sub(r"\):\s*Record<string,\s*any>\s*\{", ") {", code)
    return code


def _load_step_executions(raw_steps: list[dict[str, Any]]) -> tuple[StepExecution, ...]:
    return tuple(
        StepExecution(
            step_id=raw_step["step_id"],
            tool=raw_step["tool"],
            action=raw_step["action"],
            success=raw_step["success"],
            data=raw_step.get("data", {}),
            error=raw_step.get("error"),
        )
        for raw_step in raw_steps
    )
