"""Run the workflow pipeline."""

from pathlib import Path

from ai_workflow.config.constants import DEFAULT_GENERATED_OUTPUT_DIR
from ai_workflow.config.models import WorkflowConfig
from ai_workflow.engine.audit import build_audit_record, write_audit_record
from ai_workflow.engine.code_runner import run_generated_code
from ai_workflow.engine.mock_executor import execute_mock_workflow
from ai_workflow.engine.typescript_code_runner import (
    is_typescript_runtime_available,
    run_generated_typescript_code,
)
from ai_workflow.engine.validator import WorkflowValidator
from ai_workflow.engine.workflow_normalizer import normalize_workflow_inputs
from ai_workflow.engine.workflow_yaml import dump_workflow_yaml
from ai_workflow.generator.code_generator import generate_workflow_code
from ai_workflow.generator.output_writer import write_generated_outputs
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.mcp.context_gatherer import MockMCPContextGatherer
from ai_workflow.models.execution import WorkflowExecution
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    WorkflowPlan,
)
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.output import GeneratedOutputPaths
from ai_workflow.models.workflow import Workflow
from ai_workflow.orchestration.context_requirements import (
    context_from_intent,
    validate_required_context,
)
from ai_workflow.orchestration.orchestrator_agent import OrchestratorAgent
from ai_workflow.tools.tool_manifest import build_tool_manifest
from ai_workflow.tools.registry import ToolRegistry


async def run_workflow_pipeline(
    prompt: str,
    config: WorkflowConfig,
    llm_provider: BaseLLMProvider,
    registry: ToolRegistry,
    audit_dir: Path | None = None,
    output_dir: Path | None = None,
) -> WorkflowRunResult:
    tool_manifest = build_tool_manifest(registry)
    orchestrator = OrchestratorAgent(
        llm_provider=llm_provider,
        model_name=config.model_name,
        tool_manifest=tool_manifest,
        max_output_tokens=config.model_max_output_tokens,
    )
    intent = await orchestrator.detect_intent(prompt)
    mcp_context = await MockMCPContextGatherer().gather(
        user_request=prompt,
        intent=intent,
        tool_manifest=tool_manifest,
    )
    validate_required_context(intent=intent, mcp_context=mcp_context)
    plan = await orchestrator.create_plan(
        user_request=prompt,
        intent=intent,
        mcp_context=mcp_context,
    )

    workflow = await orchestrator.build_workflow(
        user_request=prompt,
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
    )
    workflow = normalize_workflow_inputs(workflow=workflow, intent=intent)
    WorkflowValidator(registry=registry).validate(workflow)

    workflow_yaml = dump_workflow_yaml(workflow)
    generated_code = generate_workflow_code(
        workflow=workflow,
        language=config.output_language,
    )
    code_verification = await orchestrator.verify_generated_code(
        user_request=prompt,
        workflow_yaml=workflow_yaml,
        generated_code=generated_code,
    )

    result = WorkflowRunResult(
        workflow=workflow,
        workflow_yaml=workflow_yaml,
        generated_code=generated_code,
        execution=_pending_execution(workflow.name),
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
        code_verification=code_verification,
    )

    output_paths = write_generated_outputs(
        result=result,
        output_dir=output_dir or DEFAULT_GENERATED_OUTPUT_DIR,
        language=config.output_language,
    )
    if not code_verification.approved:
        execution = WorkflowExecution(
            workflow_name=workflow.name,
            success=False,
            steps=(),
            error=f"LLM code verification failed: {code_verification.summary}",
        )
        return _finalize_result(
            prompt=prompt,
            workflow=workflow,
            workflow_yaml=workflow_yaml,
            generated_code=generated_code,
            execution=execution,
            intent=intent,
            mcp_context=mcp_context,
            plan=plan,
            code_verification=code_verification,
            output_paths=output_paths,
            audit_dir=audit_dir,
        )

    execution_context = _execution_context(config=config, intent=intent)
    if config.output_language == "python":
        execution = await run_generated_code(
            code_path=output_paths.generated_code_path,
            registry=registry,
            context=execution_context,
        )
    elif config.output_language == "typescript" and is_typescript_runtime_available():
        execution = await run_generated_typescript_code(
            code_path=output_paths.generated_code_path,
            registry=registry,
            context=execution_context,
        )
    else:
        execution = await execute_mock_workflow(
            workflow=workflow,
            registry=registry,
            context=execution_context,
        )

    return _finalize_result(
        prompt=prompt,
        workflow=workflow,
        workflow_yaml=workflow_yaml,
        generated_code=generated_code,
        execution=execution,
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
        code_verification=code_verification,
        output_paths=output_paths,
        audit_dir=audit_dir,
    )


def _execution_context(config: WorkflowConfig, intent: Intent) -> dict[str, str]:
    context = {"workflow_version": config.workflow_version}
    context.update(context_from_intent(intent))
    return context


def _pending_execution(workflow_name: str) -> WorkflowExecution:
    return WorkflowExecution(workflow_name=workflow_name, success=False, steps=())


def _finalize_result(
    prompt: str,
    workflow: Workflow,
    workflow_yaml: str,
    generated_code: str,
    execution: WorkflowExecution,
    intent: Intent,
    mcp_context: MCPContext,
    plan: WorkflowPlan,
    code_verification: CodeVerification,
    output_paths: GeneratedOutputPaths,
    audit_dir: Path | None,
) -> WorkflowRunResult:
    result = WorkflowRunResult(
        workflow=workflow,
        workflow_yaml=workflow_yaml,
        generated_code=generated_code,
        execution=execution,
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
        code_verification=code_verification,
        output_paths=output_paths,
    )
    audit_record = build_audit_record(prompt=prompt, result=result)
    if audit_dir:
        audit_path = write_audit_record(record=audit_record, audit_dir=audit_dir)
    else:
        audit_path = write_audit_record(record=audit_record)

    return WorkflowRunResult(
        workflow=workflow,
        workflow_yaml=workflow_yaml,
        generated_code=generated_code,
        execution=execution,
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
        code_verification=code_verification,
        audit_path=audit_path,
        output_paths=output_paths,
    )
