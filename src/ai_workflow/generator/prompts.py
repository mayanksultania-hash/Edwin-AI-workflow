"""Prompts for workflow generation."""

from ai_workflow.models.tool_manifest import ToolManifest
from ai_workflow.models.orchestration import Intent, MCPContext, WorkflowPlan
from ai_workflow.prompting.template_renderer import render_prompt_template
from ai_workflow.tools.tool_manifest import (
    build_default_tool_manifest,
    format_tool_manifest_for_prompt,
)


def build_workflow_generation_prompt(
    user_request: str,
    tool_manifest: ToolManifest | None = None,
    intent: Intent | None = None,
    mcp_context: MCPContext | None = None,
    plan: WorkflowPlan | None = None,
) -> str:
    manifest = tool_manifest or build_default_tool_manifest()
    allowed_tools = format_tool_manifest_for_prompt(manifest)
    orchestration_context = _format_orchestration_context(
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
    )

    return render_prompt_template(
        "generator/templates/workflow_generation.j2",
        {
            "allowed_tools": allowed_tools,
            "orchestration_context": orchestration_context,
            "user_request": user_request,
        },
    )


def _format_orchestration_context(
    intent: Intent | None,
    mcp_context: MCPContext | None,
    plan: WorkflowPlan | None,
) -> str:
    lines: list[str] = []

    if intent:
        lines.extend(
            [
                "Detected intent:",
                f"- name: {intent.name}",
                f"- domain: {intent.domain}",
                f"- summary: {intent.summary}",
                f"- entities: {intent.entities}",
                "",
            ]
        )

    if mcp_context:
        lines.extend(
            [
                "MCP context:",
                f"- source: {mcp_context.source}",
                f"- values: {mcp_context.values}",
                "",
            ]
        )

    if plan:
        lines.append("Plan:")
        lines.extend(f"- {line}" for line in plan.summary_lines())
        lines.append("")

    return "\n".join(lines)
