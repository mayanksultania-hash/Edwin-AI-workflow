"""CLI for running an AI workflow."""

import argparse
import asyncio
from pathlib import Path

from ai_workflow.app import run_ai_workflow
from ai_workflow.engine.workflow_file_validator import validate_workflow_yaml_file
from ai_workflow.orchestration.context_requirements import MissingContextError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an AI workflow from a prompt.")
    parser.add_argument("prompt", nargs="?", help="Natural language workflow request")
    parser.add_argument(
        "--validate-yaml",
        type=Path,
        default=None,
        help="Validate workflow YAML without running the LLM",
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

    if not args.prompt:
        print("prompt is required unless --validate-yaml is used")
        return 2

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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(run_cli(args))


if __name__ == "__main__":
    raise SystemExit(main())
