from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.app import run_ai_workflow


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
