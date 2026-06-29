"""Application entrypoint for running an AI workflow."""

from pathlib import Path

from ai_workflow.config.loader import load_config
from ai_workflow.config.constants import DEFAULT_GENERATED_OUTPUT_DIR
from ai_workflow.engine.checkpoint import write_run_checkpoint
from ai_workflow.engine.action_group_compiler import compile_action_group_to_action_service_json
from ai_workflow.engine.action_group_yaml import dump_action_group_yaml
from ai_workflow.engine.workflow_runner import run_workflow_pipeline
from ai_workflow.generator.action_group_generator import ActionGroupGenerator
from ai_workflow.generator.output_writer import (
    write_action_group_output,
    write_action_service_json_output,
)
from ai_workflow.llm.provider_factory import build_llm_provider
from ai_workflow.mcp.action_catalog_source_factory import (
    build_action_catalog_source,
    build_action_field_catalog_source,
    build_action_service_submitter,
)
from ai_workflow.mcp.action_ui_context import build_action_ui_context
from ai_workflow.models.run import ActionGroupRunResult
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.tools.default_registry import build_default_registry


async def run_ai_workflow(
    prompt: str,
    config_path: Path | None = None,
    version_path: Path | None = None,
    audit_dir: Path | None = None,
    output_dir: Path | None = None,
    checkpoint_dir: Path | None = None,
) -> WorkflowRunResult:
    if config_path and version_path:
        config = load_config(config_path=config_path, version_path=version_path)
    elif config_path:
        config = load_config(config_path=config_path)
    else:
        config = load_config()

    llm_provider = build_llm_provider(config)
    registry = build_default_registry(enabled_tools=config.enabled_tools)
    result = await run_workflow_pipeline(
        prompt=prompt,
        config=config,
        llm_provider=llm_provider,
        registry=registry,
        audit_dir=audit_dir,
        output_dir=output_dir,
    )
    if checkpoint_dir:
        write_run_checkpoint(
            prompt=prompt,
            result=result,
            checkpoint_dir=checkpoint_dir,
        )

    return result


async def run_action_group_workflow(
    prompt: str,
    config_path: Path | None = None,
    version_path: Path | None = None,
    output_dir: Path | None = None,
    submit: bool = False,
) -> ActionGroupRunResult:
    if config_path and version_path:
        config = load_config(config_path=config_path, version_path=version_path)
    elif config_path:
        config = load_config(config_path=config_path)
    else:
        config = load_config()

    action_ui_context = build_action_ui_context(
        catalog_source=build_action_catalog_source(config),
        field_catalog_source=build_action_field_catalog_source(config),
    )
    action_group = await ActionGroupGenerator(
        llm_provider=build_llm_provider(config),
        model_name=config.model_name,
        action_ui_context=action_ui_context,
        max_output_tokens=config.model_max_output_tokens,
    ).generate(prompt)
    action_service_json = compile_action_group_to_action_service_json(
        action_group=action_group,
        catalog=action_ui_context.catalog,
    )
    generated_output_dir = output_dir or DEFAULT_GENERATED_OUTPUT_DIR
    action_group_output_paths = write_action_group_output(
        action_group=action_group,
        output_dir=generated_output_dir,
    )
    action_service_json_output_paths = write_action_service_json_output(
        action_group_name=action_group.name,
        action_service_json=action_service_json,
        output_dir=generated_output_dir,
    )
    submit_result = None
    if submit:
        submit_result = build_action_service_submitter(config).submit_action_group(
            action_service_json
        )

    return ActionGroupRunResult(
        action_group=action_group,
        action_group_yaml=dump_action_group_yaml(action_group),
        action_service_json=action_service_json,
        action_group_output_paths=action_group_output_paths,
        action_service_json_output_paths=action_service_json_output_paths,
        submit_result=submit_result,
    )
