from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.app import run_action_group_workflow, run_ai_workflow


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_run_ai_workflow_returns_yaml_code_and_execution(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
  api_key_env_var: OPENAI_API_KEY
generation:
  output_language: python
execution:
  mode: mock
tools:
  enabled:
    - event_tool
    - alert_tool
    - servicenow_tool
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    result = asyncio.run(
        run_ai_workflow(
            prompt="When critical router event happens, create alert and incident",
            config_path=config_path,
            version_path=version_path,
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert result.workflow.name == "critical_router_event_workflow"
    assert "workflow:" in result.workflow_yaml
    assert "async def main(context: dict[str, Any], tools: dict[str, Any])" in result.generated_code
    assert result.execution.success is True
    assert result.execution.final_data["incident"]["severity"] == "critical"
    assert result.audit_path is not None
    assert result.audit_path.exists()
    assert result.output_paths is not None
    assert result.output_paths.workflow_yaml_path.exists()
    assert result.output_paths.generated_code_path.exists()


def test_run_ai_workflow_uses_configured_typescript_output(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
generation:
  output_language: typescript
execution:
  mode: mock
tools:
  enabled:
    - event_tool
    - alert_tool
    - servicenow_tool
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    result = asyncio.run(
        run_ai_workflow(
            prompt="Create workflow",
            config_path=config_path,
            version_path=version_path,
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert "export async function main(" in result.generated_code


def test_run_action_group_workflow_returns_yaml_and_action_service_json(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
generation:
  output_language: python
execution:
  mode: mock
action_fields:
  source: static
tools:
  enabled:
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    result = asyncio.run(
        run_action_group_workflow(
            prompt="Create an Incident Processing action group",
            config_path=config_path,
            version_path=version_path,
            output_dir=tmp_path / "generated",
        )
    )

    assert result.action_group.name == "Incident Processing v3.0"
    assert "action_group:" in result.action_group_yaml
    assert result.action_service_json["schemaType"] == "action_group"
    assert result.action_service_json["inputType"] == "sncIncident"
    assert len(result.action_service_json["actions"]) == 8
    assert result.action_group_output_paths is not None
    assert result.action_group_output_paths.action_group_yaml_path.exists()
    assert result.action_service_json_output_paths is not None
    assert result.action_service_json_output_paths.action_service_json_path.exists()
    assert result.submit_result is None


def test_run_action_group_workflow_can_request_submit_with_disabled_submitter(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
generation:
  output_language: python
execution:
  mode: mock
action_service:
  submit_mode: disabled
tools:
  enabled:
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    result = asyncio.run(
        run_action_group_workflow(
            prompt="Create an Incident Processing action group",
            config_path=config_path,
            version_path=version_path,
            output_dir=tmp_path / "generated",
            submit=True,
        )
    )

    assert result.submit_result is not None
    assert result.submit_result.submitted is False
    assert result.submit_result.message == "Action Service submit is disabled"
