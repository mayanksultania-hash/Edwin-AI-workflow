from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.generator.prompts import build_workflow_generation_prompt
from ai_workflow.models.orchestration import Intent, MCPContext, PlanStep, WorkflowPlan
from ai_workflow.models.tool_manifest import ToolActionManifest, ToolManifest


def test_workflow_generation_prompt_requires_yaml_only():
    prompt = build_workflow_generation_prompt("Create alert workflow")

    assert "Return only YAML." in prompt
    assert "Do not include markdown fences." in prompt
    assert "Do not include explanations." in prompt


def test_workflow_generation_prompt_lists_allowed_tools():
    prompt = build_workflow_generation_prompt("Create alert workflow")

    assert "event_tool.match_event" in prompt
    assert "alert_tool.create_or_update_alert" in prompt
    assert "servicenow_tool.create_incident" in prompt
    assert "access_tool.request_access" in prompt
    assert "access_tool.grant_access" in prompt


def test_workflow_generation_prompt_includes_access_input_hint():
    prompt = build_workflow_generation_prompt("Give John Tableau access")

    assert "access_tool.request_access should use user and system keys." in prompt
    assert "access_tool.request_access returns access_request and request." in prompt
    assert "prefer $context.user and $context.system" in prompt


def test_workflow_generation_prompt_accepts_tool_manifest():
    manifest = ToolManifest(
        actions=(
            ToolActionManifest(tool="custom_tool", action="custom_action"),
        )
    )

    prompt = build_workflow_generation_prompt(
        user_request="Create custom workflow",
        tool_manifest=manifest,
    )

    assert "custom_tool.custom_action" in prompt
    assert "event_tool.match_event" not in prompt


def test_workflow_generation_prompt_includes_orchestration_context():
    intent = Intent(
        name="access_request",
        domain="identity_access",
        summary="Create an access workflow",
        entities={"user": "John", "system": "Tableau"},
    )
    context = MCPContext(source="mock_mcp", values={"intent": "access_request"})
    plan = WorkflowPlan(
        intent=intent,
        steps=(
            PlanStep(
                order=1,
                goal="Request Tableau access for John",
                tool="access_tool",
                action="request_access",
            ),
        ),
    )

    prompt = build_workflow_generation_prompt(
        user_request="Give John Tableau access",
        intent=intent,
        mcp_context=context,
        plan=plan,
    )

    assert "Detected intent:" in prompt
    assert "- name: access_request" in prompt
    assert "MCP context:" in prompt
    assert "- source: mock_mcp" in prompt
    assert "Plan:" in prompt
    assert "- 1. Request Tableau access for John using access_tool.request_access" in prompt


def test_workflow_generation_prompt_includes_user_request():
    prompt = build_workflow_generation_prompt("When router event is critical")

    assert "User request:" in prompt
    assert "When router event is critical" in prompt
