"""Generate Action Group models from natural language."""

from dataclasses import dataclass

from ai_workflow.engine.action_group_validator import validate_action_group_with_context
from ai_workflow.engine.action_group_yaml import load_action_group_yaml
from ai_workflow.generator.prompts import build_action_group_generation_prompt
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.mcp.action_ui_context import (
    ActionUiContext,
    build_default_action_ui_context,
)
from ai_workflow.models.action_group import ActionGroup
from ai_workflow.models.llm import LLMRequest


@dataclass(frozen=True)
class ActionGroupGenerator:
    llm_provider: BaseLLMProvider
    model_name: str
    action_ui_context: ActionUiContext | None = None
    max_output_tokens: int | None = None

    async def generate(self, user_request: str) -> ActionGroup:
        context = self.action_ui_context or build_default_action_ui_context()
        prompt = build_action_group_generation_prompt(
            user_request=user_request,
            action_ui_context=context,
        )
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=prompt,
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )

        action_group = load_action_group_yaml(response.text)
        validate_action_group_with_context(action_group=action_group, context=context)
        return action_group


async def generate_action_group(
    prompt: str,
    model_name: str,
    llm_provider: BaseLLMProvider,
    action_ui_context: ActionUiContext | None = None,
    max_output_tokens: int | None = None,
) -> ActionGroup:
    return await ActionGroupGenerator(
        llm_provider=llm_provider,
        model_name=model_name,
        action_ui_context=action_ui_context,
        max_output_tokens=max_output_tokens,
    ).generate(prompt)
