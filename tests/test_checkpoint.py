from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.checkpoint import build_run_checkpoint, write_run_checkpoint
from ai_workflow.models.execution import StepExecution, WorkflowExecution
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    PlanStep,
    WorkflowPlan,
)
from ai_workflow.models.output import GeneratedOutputPaths
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.workflow import Step, Trigger, Workflow


def sample_result(tmp_path):
    intent = Intent(
        name="incident_workflow",
        domain="incident_management",
        summary="Create incident",
        entities={"event_type": "critical router event"},
    )
    plan = WorkflowPlan(
        intent=intent,
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
    return WorkflowRunResult(
        workflow=Workflow(
            name="incident_workflow",
            version="v0.1",
            trigger=Trigger(type="natural_language", description="event"),
            steps=(Step(id="match_event", tool="event_tool", action="match_event"),),
        ),
        workflow_yaml="workflow:\n",
        generated_code="code",
        execution=WorkflowExecution(
            workflow_name="incident_workflow",
            success=True,
            steps=(
                StepExecution(
                    step_id="match_event",
                    tool="event_tool",
                    action="match_event",
                    success=True,
                ),
            ),
            final_data={"status": "ok"},
        ),
        intent=intent,
        mcp_context=MCPContext(source="mock_mcp", values={"context_keys": []}),
        plan=plan,
        code_verification=CodeVerification(
            approved=True,
            risk_level="low",
            summary="Generated code matches the workflow.",
            issues=(),
        ),
        audit_path=tmp_path / "audit.json",
        output_paths=GeneratedOutputPaths(
            workflow_yaml_path=tmp_path / "workflow.yaml",
            generated_code_path=tmp_path / "workflow.py",
        ),
    )


def test_build_run_checkpoint_contains_critical_stages(tmp_path):
    checkpoint = build_run_checkpoint(
        prompt="Create event workflow",
        result=sample_result(tmp_path),
        run_id="run-1",
    )

    assert checkpoint["run_id"] == "run-1"
    assert checkpoint["prompt"] == "Create event workflow"
    assert checkpoint["checkpoints"]["intent"]["name"] == "incident_workflow"
    assert checkpoint["checkpoints"]["mcp_context"]["source"] == "mock_mcp"
    assert checkpoint["checkpoints"]["plan"]["steps"][0]["tool"] == "event_tool"
    assert checkpoint["checkpoints"]["workflow_yaml"] == "workflow:\n"
    assert checkpoint["checkpoints"]["generated_code"] == "code"
    assert checkpoint["checkpoints"]["code_verification"]["approved"] is True
    assert checkpoint["checkpoints"]["execution"]["success"] is True


def test_write_run_checkpoint_writes_single_json_file(tmp_path):
    path = write_run_checkpoint(
        prompt="Create event workflow",
        result=sample_result(tmp_path),
        checkpoint_dir=tmp_path / "checkpoints",
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == tmp_path / "checkpoints"
    assert data["checkpoints"]["execution"]["final_data"] == {"status": "ok"}
