"""Application entrypoint for running an AI workflow."""

from pathlib import Path

from ai_workflow.config.loader import load_config
from ai_workflow.engine.checkpoint import write_run_checkpoint
from ai_workflow.engine.workflow_runner import run_workflow_pipeline
from ai_workflow.llm.provider_factory import build_llm_provider
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
