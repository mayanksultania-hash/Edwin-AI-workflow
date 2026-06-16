"""Generate workflow models from natural language."""

from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.generator.prompts import build_workflow_generation_prompt
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMRequest
from ai_workflow.models.orchestration import Intent, MCPContext, WorkflowPlan
from ai_workflow.models.tool_manifest import ToolManifest
from ai_workflow.models.workflow import Workflow


async def generate_workflow(
    prompt: str,
    model_name: str,
    llm_provider: BaseLLMProvider,
    tool_manifest: ToolManifest | None = None,
    max_output_tokens: int | None = None,
    intent: Intent | None = None,
    mcp_context: MCPContext | None = None,
    plan: WorkflowPlan | None = None,
) -> Workflow:
    generation_prompt = build_workflow_generation_prompt(
        user_request=prompt,
        tool_manifest=tool_manifest,
        intent=intent,
        mcp_context=mcp_context,
        plan=plan,
    )
    response = await llm_provider.generate(
        LLMRequest(
            prompt=generation_prompt,
            model_name=model_name,
            max_output_tokens=max_output_tokens,
        )
    )

    return load_workflow_yaml(response.text)
