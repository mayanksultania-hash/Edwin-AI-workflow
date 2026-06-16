"""LLM-backed orchestrator for intent, plan, and workflow creation."""

from ai_workflow.generator.workflow_generator import generate_workflow
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMRequest
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    WorkflowPlan,
)
from ai_workflow.models.tool_manifest import ToolManifest
from ai_workflow.models.workflow import Workflow
from ai_workflow.orchestration.parsers import (
    parse_code_verification_json,
    parse_intent_json,
    parse_plan_json,
)
from ai_workflow.orchestration.plan_validator import normalize_and_validate_plan
from ai_workflow.orchestration.prompts import (
    build_code_verification_prompt,
    build_intent_prompt,
    build_plan_prompt,
)


class OrchestratorAgent:
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        model_name: str,
        tool_manifest: ToolManifest,
        max_output_tokens: int | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.tool_manifest = tool_manifest
        self.max_output_tokens = max_output_tokens

    async def detect_intent(self, user_request: str) -> Intent:
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=build_intent_prompt(user_request),
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )
        return parse_intent_json(response.text)

    async def create_plan(
        self,
        user_request: str,
        intent: Intent,
        mcp_context: MCPContext,
    ) -> WorkflowPlan:
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=build_plan_prompt(
                    user_request=user_request,
                    intent=intent,
                    mcp_context=mcp_context,
                    tool_manifest=self.tool_manifest,
                ),
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )
        plan = parse_plan_json(response.text, intent=intent)
        return normalize_and_validate_plan(plan, self.tool_manifest)

    async def build_workflow(
        self,
        user_request: str,
        intent: Intent,
        mcp_context: MCPContext,
        plan: WorkflowPlan,
    ) -> Workflow:
        return await generate_workflow(
            prompt=user_request,
            model_name=self.model_name,
            llm_provider=self.llm_provider,
            tool_manifest=self.tool_manifest,
            max_output_tokens=self.max_output_tokens,
            intent=intent,
            mcp_context=mcp_context,
            plan=plan,
        )

    async def verify_generated_code(
        self,
        user_request: str,
        workflow_yaml: str,
        generated_code: str,
    ) -> CodeVerification:
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=build_code_verification_prompt(
                    user_request=user_request,
                    workflow_yaml=workflow_yaml,
                    generated_code=generated_code,
                ),
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )
        return parse_code_verification_json(response.text)
