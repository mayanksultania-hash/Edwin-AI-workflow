from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.generator.output_writer import (
    write_action_group_output,
    write_action_service_json_output,
    write_generated_outputs,
)
from ai_workflow.models.action_group import ActionGroup, ActionStep
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


def test_write_action_group_output_writes_yaml_file(tmp_path):
    action_group = ActionGroup(
        name="Incident Processing v3.0",
        description="Process ServiceNow incident updates",
        source="sncIncident",
        rule=None,
        steps=(
            ActionStep(
                order=1,
                id="lookup_incident_reference",
                action_type="Lookup internal rowkey",
                name="Lookup Incident reference",
                description="Lookup Incident reference",
            ),
        ),
    )

    paths = write_action_group_output(action_group=action_group, output_dir=tmp_path)

    assert (
        paths.action_group_yaml_path
        == tmp_path / "action_groups" / "incident_processing_v3_0.yaml"
    )
    content = paths.action_group_yaml_path.read_text(encoding="utf-8")
    assert content.startswith("action_group:")
    assert "name: Incident Processing v3.0" in content


def test_write_action_service_json_output_writes_json_file(tmp_path):
    paths = write_action_service_json_output(
        action_group_name="Create an Incident",
        action_service_json={"schemaType": "action_group", "name": "Create an Incident"},
        output_dir=tmp_path,
    )

    assert (
        paths.action_service_json_path
        == tmp_path / "action_service_json" / "create_an_incident.json"
    )
    assert '"schemaType": "action_group"' in paths.action_service_json_path.read_text(
        encoding="utf-8"
    )
