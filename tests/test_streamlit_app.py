from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.execution import StepExecution, WorkflowExecution
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    PlanStep,
    WorkflowPlan,
)
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.tool_manifest import ToolActionManifest, ToolManifest
from ai_workflow.models.workflow import Step, Trigger, Workflow
from ai_workflow.ui.streamlit_app import (
    code_verification_summary,
    dry_run_summary,
    execution_steps_table,
    intent_summary,
    mcp_context_summary,
    plan_steps_table,
    tool_manifest_table,
)


def test_execution_steps_table_returns_display_rows():
    execution = WorkflowExecution(
        workflow_name="sample",
        success=True,
        steps=(
            StepExecution(
                step_id="check_event",
                tool="event_tool",
                action="match_event",
                success=True,
            ),
        ),
    )

    rows = execution_steps_table(execution)

    assert rows == [
        {
            "step_id": "check_event",
            "tool": "event_tool",
            "action": "match_event",
            "success": True,
            "error": "",
        }
    ]


def test_tool_manifest_table_returns_display_rows():
    manifest = ToolManifest(
        actions=(
            ToolActionManifest(tool="event_tool", action="match_event"),
            ToolActionManifest(tool="access_tool", action="request_access"),
        )
    )

    rows = tool_manifest_table(manifest)

    assert rows == [
        {"tool": "event_tool", "action": "match_event"},
        {"tool": "access_tool", "action": "request_access"},
    ]


def test_intent_summary_returns_display_data():
    intent = Intent(
        name="incident_workflow",
        domain="incident_management",
        summary="Create incident",
        entities={"event_type": "critical router event"},
    )

    assert intent_summary(intent) == {
        "name": "incident_workflow",
        "domain": "incident_management",
        "summary": "Create incident",
        "entities": {"event_type": "critical router event"},
    }


def test_mcp_context_summary_returns_display_data():
    context = MCPContext(
        source="mock_mcp",
        values={"context_keys": ["event_type"]},
    )

    assert mcp_context_summary(context) == {
        "source": "mock_mcp",
        "values": {"context_keys": ["event_type"]},
    }


def test_plan_steps_table_returns_display_rows():
    plan = WorkflowPlan(
        intent=Intent(
            name="incident_workflow",
            domain="incident_management",
            summary="Create incident",
        ),
        steps=(
            PlanStep(
                order=1,
                goal="Match event",
                tool="event_tool",
                action="match_event",
                inputs={"event_type": "$context.event_type"},
            ),
        ),
    )

    assert plan_steps_table(plan) == [
        {
            "order": 1,
            "goal": "Match event",
            "tool": "event_tool",
            "action": "match_event",
            "inputs": {"event_type": "$context.event_type"},
        }
    ]


def test_code_verification_summary_returns_display_data():
    verification = CodeVerification(
        approved=True,
        risk_level="low",
        summary="Generated code looks correct.",
        issues=("none",),
    )

    assert code_verification_summary(verification) == {
        "approved": True,
        "risk_level": "low",
        "summary": "Generated code looks correct.",
        "issues": ["none"],
    }


def test_dry_run_summary_describes_successful_run():
    workflow = Workflow(
        name="sample_workflow",
        version="v0.1",
        trigger=Trigger(type="natural_language", description="sample"),
        steps=(
            Step(
                id="check_event",
                tool="event_tool",
                action="match_event",
            ),
        ),
    )
    result = WorkflowRunResult(
        workflow=workflow,
        workflow_yaml="workflow:\n",
        generated_code="code",
        execution=WorkflowExecution(
            workflow_name="sample_workflow",
            success=True,
            steps=(),
        ),
    )

    summary = dry_run_summary(result)

    assert "Created workflow `sample_workflow`." in summary
    assert "Executed mock tools only." in summary
    assert "Finished successfully." in summary
