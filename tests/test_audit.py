from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.audit import build_audit_record, write_audit_record
from ai_workflow.models.execution import WorkflowExecution
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.workflow import Trigger, Workflow


def sample_run_result():
    workflow = Workflow(
        name="sample_workflow",
        version="v0.1",
        trigger=Trigger(type="natural_language", description="sample"),
        steps=(),
    )
    return WorkflowRunResult(
        workflow=workflow,
        workflow_yaml="workflow:\n  name: sample_workflow\n",
        generated_code="async def sample_workflow(context):\n    return context\n",
        execution=WorkflowExecution(
            workflow_name="sample_workflow",
            success=True,
            steps=(),
            final_data={"status": "ok"},
        ),
    )


def test_build_audit_record_from_run_result():
    record = build_audit_record(
        prompt="Create workflow",
        result=sample_run_result(),
    )

    assert record.prompt == "Create workflow"
    assert record.workflow_name == "sample_workflow"
    assert record.execution_success is True
    assert record.final_data == {"status": "ok"}
    assert record.run_id
    assert record.created_at


def test_write_audit_record_writes_json_file(tmp_path):
    record = build_audit_record(
        prompt="Create workflow",
        result=sample_run_result(),
    )

    audit_path = write_audit_record(record, audit_dir=tmp_path)

    data = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit_path.name == f"{record.run_id}.json"
    assert data["prompt"] == "Create workflow"
    assert data["workflow_name"] == "sample_workflow"
    assert data["final_data"] == {"status": "ok"}
