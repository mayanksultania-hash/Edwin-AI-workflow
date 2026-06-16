from pathlib import Path
import argparse
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.main import build_parser, run_cli
from ai_workflow.orchestration.context_requirements import MissingContextError


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_build_parser_reads_prompt():
    args = build_parser().parse_args(["Create workflow"])

    assert args.prompt == "Create workflow"
    assert args.validate_yaml is None
    assert args.config is None
    assert args.version is None
    assert args.audit_dir is None
    assert args.output_dir is None


def test_build_parser_reads_output_paths(tmp_path):
    args = build_parser().parse_args(
        [
            "Create workflow",
            "--audit-dir",
            str(tmp_path / "audit"),
            "--output-dir",
            str(tmp_path / "generated"),
        ]
    )

    assert args.audit_dir == tmp_path / "audit"
    assert args.output_dir == tmp_path / "generated"


def test_build_parser_reads_validate_yaml_path(tmp_path):
    args = build_parser().parse_args(["--validate-yaml", str(tmp_path / "workflow.yaml")])

    assert args.prompt is None
    assert args.validate_yaml == tmp_path / "workflow.yaml"


def test_run_cli_prints_workflow_outputs(tmp_path, capsys):
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
tools:
  enabled:
    - event_tool
    - alert_tool
    - servicenow_tool
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt="Create workflow",
                validate_yaml=None,
                config=config_path,
                version=version_path,
                audit_dir=tmp_path / "audit",
                output_dir=tmp_path / "generated",
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Intent" in output
    assert "## MCP Context" in output
    assert "## Plan" in output
    assert "## Workflow YAML" in output
    assert "## Generated Code" in output
    assert "## Execution" in output
    assert "## Files" in output
    assert "success: True" in output
    assert "workflow_yaml_path:" in output
    assert "generated_code_path:" in output


def test_run_cli_validates_workflow_yaml(tmp_path, capsys):
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
tools:
  enabled:
    - event_tool
""",
    )
    workflow_path = write_file(
        tmp_path / "workflow.yaml",
        """
workflow:
  name: event_only_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: event only
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
""",
    )

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt=None,
                validate_yaml=workflow_path,
                config=config_path,
                version=None,
                audit_dir=None,
                output_dir=None,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Workflow Validation" in output
    assert "valid: True" in output
    assert "name: event_only_workflow" in output
    assert "steps: 1" in output


def test_run_cli_prints_missing_context_questions(monkeypatch, capsys):
    async def fake_run_ai_workflow(**kwargs):
        raise MissingContextError(
            missing_keys=("user",),
            questions=("Who should this workflow run for?",),
        )

    monkeypatch.setattr("ai_workflow.main.run_ai_workflow", fake_run_ai_workflow)

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt="Give Tableau access",
                validate_yaml=None,
                config=None,
                version=None,
                audit_dir=None,
                output_dir=None,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "## Missing Context" in output
    assert "missing_keys: ['user']" in output
    assert "- Who should this workflow run for?" in output
