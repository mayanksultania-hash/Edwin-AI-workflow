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
    assert args.action_group is False
    assert args.validate_yaml is None
    assert args.validate_action_group_yaml is None
    assert args.compile_action_group_yaml is None
    assert args.show_action_catalog is False
    assert args.config is None
    assert args.version is None
    assert args.audit_dir is None
    assert args.output_dir is None


def test_build_parser_reads_action_group_flag():
    args = build_parser().parse_args(["Create action group", "--action-group"])

    assert args.prompt == "Create action group"
    assert args.action_group is True


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


def test_build_parser_reads_validate_action_group_yaml_path(tmp_path):
    args = build_parser().parse_args(
        ["--validate-action-group-yaml", str(tmp_path / "action_group.yaml")]
    )

    assert args.prompt is None
    assert args.validate_action_group_yaml == tmp_path / "action_group.yaml"


def test_build_parser_reads_compile_action_group_yaml_path(tmp_path):
    args = build_parser().parse_args(
        ["--compile-action-group-yaml", str(tmp_path / "action_group.yaml")]
    )

    assert args.prompt is None
    assert args.compile_action_group_yaml == tmp_path / "action_group.yaml"


def test_build_parser_reads_show_action_catalog_flag():
    args = build_parser().parse_args(["--show-action-catalog"])

    assert args.prompt is None
    assert args.show_action_catalog is True


def test_run_cli_prints_action_catalog(tmp_path, capsys):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
generation:
  output_language: python
execution:
  mode: mock
action_catalog:
  source: static
tools:
  enabled:
""",
    )

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt=None,
                action_group=False,
                validate_yaml=None,
                validate_action_group_yaml=None,
                show_action_catalog=True,
                config=config_path,
                version=None,
                audit_dir=None,
                output_dir=None,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Action Catalog" in output
    assert "source: static" in output
    assert "actions: 8" in output
    assert "- Update Insight" in output
    assert "record_type: insights" in output
    assert "config_fields: ['add_additional_alerts']" in output


def test_run_cli_prints_action_group_yaml(tmp_path, capsys):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
  max_output_tokens: 1200
generation:
  output_language: python
execution:
  mode: mock
tools:
  enabled:
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.1\n")

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt="Create an Incident Processing action group",
                action_group=True,
                validate_yaml=None,
                config=config_path,
                version=version_path,
                audit_dir=None,
                output_dir=tmp_path / "generated",
                show_action_catalog=False,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Action Group YAML" in output
    assert "action_group:" in output
    assert "name: Incident Processing v3.0" in output
    assert "action_type: Update SNC Incident" in output
    assert "## Validation" in output
    assert "valid: True" in output
    assert "steps: 8" in output
    assert "## Files" in output
    assert "action_group_yaml_path:" in output
    assert (
        tmp_path
        / "generated"
        / "action_groups"
        / "incident_processing_v3_0.yaml"
    ).exists()


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
                show_action_catalog=False,
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
                show_action_catalog=False,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Workflow Validation" in output
    assert "valid: True" in output
    assert "name: event_only_workflow" in output
    assert "steps: 1" in output


def test_run_cli_validates_action_group_yaml(tmp_path, capsys):
    action_group_path = write_file(
        tmp_path / "action_group.yaml",
        """
action_group:
  name: Incident Processing v3.0
  description: Process ServiceNow incident updates
  source: sncIncident
  rule:
  steps:
    - order: 1
      id: lookup_incident_reference
      action_type: Lookup internal rowkey
      name: Lookup Incident reference
      description: Lookup Incident reference
""",
    )

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt=None,
                action_group=False,
                validate_yaml=None,
                validate_action_group_yaml=action_group_path,
                config=None,
                version=None,
                audit_dir=None,
                output_dir=None,
                show_action_catalog=False,
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Action Group Validation" in output
    assert "valid: True" in output
    assert f"path: {action_group_path}" in output
    assert "name: Incident Processing v3.0" in output
    assert "source: sncIncident" in output
    assert "steps: 1" in output


def test_run_cli_compiles_action_group_yaml(tmp_path, capsys):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
generation:
  output_language: python
execution:
  mode: mock
tools:
  enabled:
""",
    )
    action_group_path = write_file(
        tmp_path / "action_group.yaml",
        """
action_group:
  name: Incident Processing v3.0
  description: Process ServiceNow incident updates
  source: sncIncident
  rule:
  steps:
    - order: 1
      id: lookup_incident_reference
      action_type: Lookup internal rowkey
      name: Lookup Incident reference
      description: Lookup Incident reference
""",
    )

    exit_code = asyncio.run(
        run_cli(
            argparse.Namespace(
                prompt=None,
                action_group=False,
                validate_yaml=None,
                validate_action_group_yaml=None,
                compile_action_group_yaml=action_group_path,
                show_action_catalog=False,
                config=config_path,
                version=None,
                audit_dir=None,
                output_dir=tmp_path / "generated",
            )
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## Action Service JSON" in output
    assert '"schemaType": "action_group"' in output
    assert '"inputType": "sncIncident"' in output
    assert '"actionId": "mock-lookup-internal-rowkey"' in output
    assert "## Files" in output
    assert "action_service_json_path:" in output
    assert (
        tmp_path
        / "generated"
        / "action_service_json"
        / "incident_processing_v3_0.json"
    ).exists()


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
