"""CLI for running an AI workflow."""

import argparse
import asyncio
import json
from pathlib import Path

from ai_workflow.app import run_ai_workflow
from ai_workflow.config.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_GENERATED_OUTPUT_DIR,
    VERSION_FILE_PATH,
)
from ai_workflow.config.loader import load_config
from ai_workflow.engine.action_group_compiler import (
    compile_action_group_to_action_service_json,
)
from ai_workflow.engine.action_group_validator import validate_action_group_with_context
from ai_workflow.engine.action_group_yaml import (
    dump_action_group_yaml,
    load_action_group_yaml_file,
)
from ai_workflow.engine.workflow_file_validator import validate_workflow_yaml_file
from ai_workflow.generator.action_group_generator import ActionGroupGenerator
from ai_workflow.generator.output_writer import (
    write_action_group_output,
    write_action_service_json_output,
)
from ai_workflow.llm.provider_factory import build_llm_provider
from ai_workflow.mcp.action_catalog_source_factory import (
    build_action_catalog_source,
    build_action_field_catalog_source,
)
from ai_workflow.mcp.action_ui_context import build_action_ui_context
from ai_workflow.orchestration.context_requirements import MissingContextError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an AI workflow from a prompt.")
    parser.add_argument("prompt", nargs="?", help="Natural language workflow request")
    parser.add_argument(
        "--action-group",
        action="store_true",
        help="Generate Action Group YAML from the prompt",
    )
    parser.add_argument(
        "--validate-yaml",
        type=Path,
        default=None,
        help="Validate workflow YAML without running the LLM",
    )
    parser.add_argument(
        "--validate-action-group-yaml",
        type=Path,
        default=None,
        help="Validate Action Group YAML without running the LLM",
    )
    parser.add_argument(
        "--compile-action-group-yaml",
        type=Path,
        default=None,
        help="Compile Action Group YAML to Action Service JSON without running the LLM",
    )
    parser.add_argument(
        "--show-action-catalog",
        action="store_true",
        help="Print the configured Action Service catalog without running the LLM",
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config YAML")
    parser.add_argument("--version", type=Path, default=None, help="Path to VERSION file")
    parser.add_argument("--audit-dir", type=Path, default=None, help="Audit output folder")
    parser.add_argument("--output-dir", type=Path, default=None, help="Generated output folder")
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=None,
        help="Detailed checkpoint output folder",
    )
    return parser


async def run_cli(args: argparse.Namespace) -> int:
    if getattr(args, "show_action_catalog", False):
        config = _load_cli_config(args)
        action_ui_context = _build_action_ui_context(config)
        print("## Action Catalog")
        print(f"source: {config.action_catalog_source}")
        if config.action_catalog_base_url:
            print(f"base_url: {config.action_catalog_base_url}")
        print(f"actions: {len(action_ui_context.catalog.actions)}")
        for action in action_ui_context.catalog.actions:
            print(f"- {action.action_name}")
            print(f"  id: {action.action_id}")
            print(f"  record_type: {action.record_type}")
            print(f"  outcomes: {list(action.outcomes)}")
            print(f"  config_fields: {list(action.config_field_names())}")
        return 0

    if getattr(args, "validate_yaml", None):
        result = validate_workflow_yaml_file(
            workflow_path=args.validate_yaml,
            config_path=args.config,
            version_path=args.version,
        )
        print("## Workflow Validation")
        print(f"valid: True")
        print(f"path: {result.path}")
        print(f"name: {result.workflow.name}")
        print(f"steps: {result.step_count}")
        return 0

    if getattr(args, "validate_action_group_yaml", None):
        config = _load_cli_config(args)
        action_ui_context = _build_action_ui_context(config)
        action_group = load_action_group_yaml_file(args.validate_action_group_yaml)
        validate_action_group_with_context(
            action_group=action_group,
            context=action_ui_context,
        )
        print("## Action Group Validation")
        print("valid: True")
        print(f"path: {args.validate_action_group_yaml}")
        print(f"name: {action_group.name}")
        print(f"source: {action_group.source}")
        print(f"steps: {len(action_group.steps)}")
        return 0

    if getattr(args, "compile_action_group_yaml", None):
        config = _load_cli_config(args)
        action_ui_context = _build_action_ui_context(config)
        action_group = load_action_group_yaml_file(args.compile_action_group_yaml)
        validate_action_group_with_context(
            action_group=action_group,
            context=action_ui_context,
        )
        action_service_json = compile_action_group_to_action_service_json(
            action_group=action_group,
            catalog=action_ui_context.catalog,
        )
        output_paths = write_action_service_json_output(
            action_group_name=action_group.name,
            action_service_json=action_service_json,
            output_dir=args.output_dir or DEFAULT_GENERATED_OUTPUT_DIR,
        )

        print("## Action Service JSON")
        print(json.dumps(action_service_json, indent=2))
        print("## Files")
        print(f"action_service_json_path: {output_paths.action_service_json_path}")
        return 0

    if not args.prompt:
        print(
            "prompt is required unless --validate-yaml, "
            "--validate-action-group-yaml, --compile-action-group-yaml, "
            "or --show-action-catalog is used"
        )
        return 2

    if getattr(args, "action_group", False):
        config = _load_cli_config(args)
        action_ui_context = _build_action_ui_context(config)
        generator = ActionGroupGenerator(
            llm_provider=build_llm_provider(config),
            model_name=config.model_name,
            action_ui_context=action_ui_context,
            max_output_tokens=config.model_max_output_tokens,
        )
        action_group = await generator.generate(args.prompt)
        output_paths = write_action_group_output(
            action_group=action_group,
            output_dir=args.output_dir or DEFAULT_GENERATED_OUTPUT_DIR,
        )

        print("## Action Group YAML")
        print(dump_action_group_yaml(action_group))
        print("## Validation")
        print("valid: True")
        print(f"name: {action_group.name}")
        print(f"source: {action_group.source}")
        print(f"steps: {len(action_group.steps)}")
        print("## Files")
        print(f"action_group_yaml_path: {output_paths.action_group_yaml_path}")
        return 0

    try:
        result = await run_ai_workflow(
            prompt=args.prompt,
            config_path=args.config,
            version_path=args.version,
            audit_dir=args.audit_dir,
            output_dir=args.output_dir,
            checkpoint_dir=getattr(args, "checkpoint_dir", None),
        )
    except MissingContextError as error:
        print("## Missing Context")
        print(f"missing_keys: {list(error.missing_keys)}")
        print("questions:")
        for question in error.questions:
            print(f"- {question}")
        return 2

    print("## Intent")
    print(f"name: {result.intent.name if result.intent else ''}")
    print(f"domain: {result.intent.domain if result.intent else ''}")
    print(f"entities: {result.intent.entities if result.intent else {}}")
    print("## MCP Context")
    print(f"source: {result.mcp_context.source if result.mcp_context else ''}")
    print("## Plan")
    for line in result.plan.summary_lines() if result.plan else []:
        print(f"- {line}")
    print("## Workflow YAML")
    print(result.workflow_yaml)
    print("## Generated Code")
    print(result.generated_code)
    print("## Code Verification")
    if result.code_verification:
        print(f"approved: {result.code_verification.approved}")
        print(f"risk_level: {result.code_verification.risk_level}")
        print(f"summary: {result.code_verification.summary}")
        print(f"issues: {list(result.code_verification.issues)}")
    else:
        print("approved: ")
    print("## Execution")
    print(f"success: {result.execution.success}")
    print(f"final_data: {result.execution.final_data}")
    print("## Files")
    print(f"audit_path: {result.audit_path}")
    print(f"workflow_yaml_path: {result.output_paths.workflow_yaml_path}")
    print(f"generated_code_path: {result.output_paths.generated_code_path}")
    return 0 if result.execution.success else 1


def _load_cli_config(args: argparse.Namespace):
    return load_config(
        config_path=args.config or DEFAULT_CONFIG_PATH,
        version_path=args.version or VERSION_FILE_PATH,
    )


def _build_action_ui_context(config):
    return build_action_ui_context(
        catalog_source=build_action_catalog_source(config),
        field_catalog_source=build_action_field_catalog_source(config),
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(run_cli(args))


if __name__ == "__main__":
    raise SystemExit(main())
