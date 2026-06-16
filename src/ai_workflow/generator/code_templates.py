"""Code templates for workflow generation."""

import json
from typing import Any

from ai_workflow.models.workflow import Step, Workflow


def render_python_workflow(workflow: Workflow) -> str:
    modules = sorted({_python_integration_module(step.tool) for step in workflow.steps})
    lines = [
        "from typing import Any",
        "",
        "from ai_workflow.integrations import bind_runtime",
        f"from ai_workflow.integrations import {', '.join(modules)}",
        "",
        f"WORKFLOW_NAME = {workflow.name!r}",
        "LAST_STEP_EXECUTIONS: list[dict[str, Any]] = []",
        "",
        "async def main(context: dict[str, Any], tools: dict[str, Any]) -> dict[str, Any]:",
        "    LAST_STEP_EXECUTIONS.clear()",
        "    step_outputs: dict[str, Any] = {}",
        "    with bind_runtime(tools=tools, context=context):",
    ]

    for index, step in enumerate(workflow.steps, start=1):
        result_name = f"step_{index}_result"
        module_name = _python_integration_module(step.tool)
        lines.append(
            f"        {result_name} = await {module_name}.{step.action}("
            f"{python_call_arguments(step.inputs)})"
        )
        lines.append(f"        if not {result_name}.success:")
        lines.append(
            "            LAST_STEP_EXECUTIONS.append("
            f"{{'step_id': {step.id!r}, 'tool': {step.tool!r}, "
            f"'action': {step.action!r}, 'success': False, "
            f"'data': {result_name}.data, 'error': {result_name}.error}})"
        )
        lines.append(
            f"            raise RuntimeError({result_name}.error or "
            f"{('Step failed: ' + step.id)!r})"
        )
        lines.append(f"        step_outputs[{step.id!r}] = {result_name}.data")
        lines.append(
            "        LAST_STEP_EXECUTIONS.append("
            f"{{'step_id': {step.id!r}, 'tool': {step.tool!r}, "
            f"'action': {step.action!r}, 'success': True, "
            f"'data': {result_name}.data, 'error': None}})"
        )

    lines.append(f"        return step_outputs[{workflow.steps[-1].id!r}]")
    return "\n".join(lines) + "\n"


def render_typescript_workflow(workflow: Workflow) -> str:
    lines = [
        f"export const workflowName = {json.dumps(workflow.name)};",
        "export const lastStepExecutions: Array<Record<string, any>> = [];",
        "",
        "function createIntegration(",
        "  toolName: string,",
        "  tools: Record<string, any>,",
        "  context: Record<string, any>,",
        "): Record<string, any> {",
        "  return new Proxy({}, {",
        "    get: (_target, action: string) => (inputs: Record<string, any>) =>",
        "        tools[toolName].execute({ action, inputs, context }),",
        "  });",
        "}",
        "",
        "export async function main(",
        "  context: Record<string, any>,",
        "  tools: Record<string, any>,",
        "): Promise<Record<string, any>> {",
        "  lastStepExecutions.length = 0;",
        *_typescript_integration_lines(workflow),
        "  const stepOutputs: Record<string, any> = {};",
    ]

    for index, step in enumerate(workflow.steps, start=1):
        result_name = f"step{index}Result"
        integration_name = _typescript_integration_name(step.tool)
        lines.append(
            f"  const {result_name} = await {integration_name}.{step.action}("
        )
        lines.extend(typescript_call_argument_lines(step.inputs, indent="    "))
        lines.append("  );")
        lines.append(f"  if (!{result_name}.success) {{")
        lines.append(
            "    lastStepExecutions.push("
            f"{{ step_id: {json.dumps(step.id)}, tool: {json.dumps(step.tool)}, "
            f"action: {json.dumps(step.action)}, success: false, "
            f"data: {result_name}.data, error: {result_name}.error }});"
        )
        lines.append(
            f"    throw new Error({result_name}.error ?? "
            f"{json.dumps('Step failed: ' + step.id)});"
        )
        lines.append("  }")
        lines.append(f"  stepOutputs[{json.dumps(step.id)}] = {result_name}.data;")
        lines.append(
            "  lastStepExecutions.push("
            f"{{ step_id: {json.dumps(step.id)}, tool: {json.dumps(step.tool)}, "
            f"action: {json.dumps(step.action)}, success: true, "
            f"data: {result_name}.data, error: null }});"
        )

    lines.append(f"  return stepOutputs[{json.dumps(workflow.steps[-1].id)}];")
    lines.append("}")
    return "\n".join(lines) + "\n"


def python_step_result_name(step: Step) -> str:
    return f"{step.id}_result"


def typescript_step_result_name(step: Step) -> str:
    return f"{to_camel_case(step.id)}Result"


def python_literal(value: dict[str, Any]) -> str:
    return repr(value)


def typescript_literal(value: dict[str, Any]) -> str:
    return json.dumps(value)


def python_inputs_literal(value: Any) -> str:
    if isinstance(value, str) and value.startswith("$"):
        return python_reference_expression(value)

    if isinstance(value, dict):
        items = [
            f"{key!r}: {python_inputs_literal(nested_value)}"
            for key, nested_value in value.items()
        ]
        return "{" + ", ".join(items) + "}"

    if isinstance(value, list):
        return "[" + ", ".join(python_inputs_literal(item) for item in value) + "]"

    return repr(value)


def python_call_arguments(value: dict[str, Any]) -> str:
    if all(isinstance(key, str) and key.isidentifier() for key in value):
        return ", ".join(
            f"{key}={python_inputs_literal(nested_value)}"
            for key, nested_value in value.items()
        )

    return f"**{python_inputs_literal(value)}"


def typescript_inputs_literal(value: Any) -> str:
    if isinstance(value, str) and value.startswith("$"):
        return typescript_reference_expression(value)

    if isinstance(value, dict):
        items = [
            f"{json.dumps(key)}: {typescript_inputs_literal(nested_value)}"
            for key, nested_value in value.items()
        ]
        return "{" + ", ".join(items) + "}"

    if isinstance(value, list):
        return "[" + ", ".join(typescript_inputs_literal(item) for item in value) + "]"

    return json.dumps(value)


def typescript_call_argument_lines(value: dict[str, Any], indent: str) -> list[str]:
    if not value:
        return [f"{indent}{{}},"]

    lines = [f"{indent}{{"]
    for key, nested_value in value.items():
        lines.append(
            f"{indent}  {json.dumps(key)}: "
            f"{typescript_inputs_literal(nested_value)},"
        )
    lines.append(f"{indent}}},")
    return lines


def python_reference_expression(reference: str) -> str:
    parts = reference.split(".")
    if len(parts) < 2:
        return repr(reference)

    if parts[0] == "$steps" and len(parts) >= 3:
        expression = f"step_outputs[{parts[1]!r}]"
        return _append_python_path(expression, parts[2:])

    if parts[0] == "$context":
        return _append_python_path("context", parts[1:])

    return repr(reference)


def typescript_reference_expression(reference: str) -> str:
    parts = reference.split(".")
    if len(parts) < 2:
        return json.dumps(reference)

    if parts[0] == "$steps" and len(parts) >= 3:
        expression = f"stepOutputs[{json.dumps(parts[1])}]"
        return _append_typescript_path(expression, parts[2:])

    if parts[0] == "$context":
        return _append_typescript_path("context", parts[1:])

    return json.dumps(reference)


def _append_python_path(expression: str, path_parts: list[str]) -> str:
    for part in path_parts:
        expression += f"[{part!r}]"
    return expression


def _append_typescript_path(expression: str, path_parts: list[str]) -> str:
    for part in path_parts:
        expression += f"[{json.dumps(part)}]"
    return expression


def to_camel_case(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value

    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _python_integration_module(tool_name: str) -> str:
    return tool_name.removesuffix("_tool")


def _typescript_integration_name(tool_name: str) -> str:
    return to_camel_case(tool_name.removesuffix("_tool"))


def _typescript_integration_lines(workflow: Workflow) -> list[str]:
    lines = []
    seen_tools = set()
    for step in workflow.steps:
        if step.tool in seen_tools:
            continue

        seen_tools.add(step.tool)
        lines.append(
            f"  const {_typescript_integration_name(step.tool)} = "
            f"createIntegration({json.dumps(step.tool)}, tools, context);"
        )

    return lines
