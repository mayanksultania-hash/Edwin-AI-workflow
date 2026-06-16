"""Prompts for orchestration agent steps."""

from ai_workflow.models.orchestration import Intent, MCPContext
from ai_workflow.models.tool_manifest import ToolManifest
from ai_workflow.prompting.template_renderer import render_prompt_template


def build_intent_prompt(user_request: str) -> str:
    return render_prompt_template(
        "orchestration/templates/intent_detection.j2",
        {"user_request": user_request},
    )


def build_plan_prompt(
    user_request: str,
    intent: Intent,
    mcp_context: MCPContext,
    tool_manifest: ToolManifest,
) -> str:
    actions = "\n".join(f"- {name}" for name in tool_manifest.action_names())
    return render_prompt_template(
        "orchestration/templates/plan_creation.j2",
        {
            "actions": actions,
            "intent": intent,
            "mcp_context": mcp_context,
            "user_request": user_request,
        },
    )


def build_code_verification_prompt(
    user_request: str,
    workflow_yaml: str,
    generated_code: str,
) -> str:
    return render_prompt_template(
        "orchestration/templates/code_verification.j2",
        {
            "generated_code": generated_code,
            "user_request": user_request,
            "workflow_yaml": workflow_yaml,
        },
    )
