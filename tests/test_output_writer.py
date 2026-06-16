from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.generator.output_writer import write_generated_outputs
from ai_workflow.models.execution import WorkflowExecution
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.workflow import Trigger, Workflow


def sample_result():
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
        ),
    )


def test_write_generated_outputs_writes_python_files(tmp_path):
    paths = write_generated_outputs(
        result=sample_result(),
        output_dir=tmp_path,
        language="python",
    )

    assert paths.workflow_yaml_path == tmp_path / "workflows" / "sample_workflow.yaml"
    assert paths.generated_code_path == tmp_path / "code" / "sample_workflow.py"
    assert paths.workflow_yaml_path.read_text(encoding="utf-8").startswith("workflow:")
    assert "async def sample_workflow" in paths.generated_code_path.read_text(
        encoding="utf-8"
    )


def test_write_generated_outputs_writes_typescript_file(tmp_path):
    paths = write_generated_outputs(
        result=sample_result(),
        output_dir=tmp_path,
        language="typescript",
    )

    assert paths.generated_code_path == tmp_path / "code" / "sample_workflow.ts"
