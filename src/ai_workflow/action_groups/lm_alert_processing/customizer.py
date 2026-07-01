"""Guided customization for the LM Alert Processing Action Group.

This module is the orchestration entry point for LM Alert Processing guided setup.
Implementation is split across sibling sub-packages; this file wires the LLM flows
and re-exports the public API.

Sub-packages:
- ``config/action_ids/`` — reusable Action ID field sets and catalog.
- ``config/action_group/`` — LM Alert Processing step groups and guided questions.
- ``core/``     — LLM models, response parsing, YAML patches and validation.
- ``helpers/``  — file I/O, YAML step lookup, LLM JSON parsing, prompt builders.
- ``prompts/``  — Jinja templates.
"""

from dataclasses import dataclass
from pathlib import Path

from ai_workflow.action_groups.common.action_schemas.base import step_group_question_key
from ai_workflow.action_groups.lm_alert_processing.config.constants import (
    DEFAULT_BASE_YAML_PATH,
    LM_ALERT_PROCESSING_BASE_ACTION_GROUP_ID,
)
from ai_workflow.action_groups.lm_alert_processing.config.action_group import (
    build_lm_alert_action_group_step_groups,
)
from ai_workflow.action_groups.lm_alert_processing.core.llm_parsing import (
    parse_guided_questions,
    parse_yaml_patch_plan,
)
from ai_workflow.action_groups.lm_alert_processing.core.yaml_patches import apply_yaml_patches
from ai_workflow.action_groups.lm_alert_processing.core.yaml_validation import (
    validate_final_lm_alert_yaml,
)
from ai_workflow.action_groups.lm_alert_processing.helpers.io_helpers import (
    dump_yaml_text,
    load_yaml_text,
    save_final_action_group_yaml,
)
from ai_workflow.action_groups.lm_alert_processing.helpers.prompts_builder import (
    build_lm_alert_question_generation_prompt,
    build_lm_alert_yaml_patch_prompt,
)
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.action_group_customization import (
    ActionGroupYamlCustomizationResult,
    GuidedQuestion,
)
from ai_workflow.models.llm import LLMRequest

__all__ = [
    "DEFAULT_BASE_YAML_PATH",
    "LM_ALERT_PROCESSING_BASE_ACTION_GROUP_ID",
    "LMAlertProcessingCustomizer",
    "apply_yaml_patches",
    "build_lm_alert_processing_questions",
    "build_lm_alert_question_generation_prompt",
    "build_lm_alert_yaml_patch_prompt",
    "dump_yaml_text",
    "load_yaml_text",
    "parse_guided_questions",
    "parse_yaml_patch_plan",
    "save_final_action_group_yaml",
    "validate_final_lm_alert_yaml",
]


def build_lm_alert_processing_questions() -> tuple[GuidedQuestion, ...]:
    return tuple(
        GuidedQuestion(
            key=step_group_question_key(group.group_id, hint.key_suffix),
            question=hint.question,
            example_answer=hint.example_answer,
        )
        for group in build_lm_alert_action_group_step_groups()
        for hint in group.question_hints[:1]
    )


@dataclass(frozen=True)
class LMAlertProcessingCustomizer:
    llm_provider: BaseLLMProvider
    model_name: str
    base_yaml_path: Path = DEFAULT_BASE_YAML_PATH
    max_output_tokens: int | None = None

    async def generate_questions_from_base_yaml(self) -> tuple[GuidedQuestion, ...]:
        base_yaml = self.base_yaml_path.read_text(encoding="utf-8")
        prompt = build_lm_alert_question_generation_prompt(base_yaml=base_yaml)
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=prompt,
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )
        return parse_guided_questions(response.text)

    async def customize_base_yaml(
        self,
        answers: dict[str, str],
        output_dir: Path,
        questions: tuple[GuidedQuestion, ...] | None = None,
    ) -> ActionGroupYamlCustomizationResult:
        base_yaml = self.base_yaml_path.read_text(encoding="utf-8")
        prompt = build_lm_alert_yaml_patch_prompt(
            base_yaml=base_yaml,
            answers=answers,
        )
        response = await self.llm_provider.generate(
            LLMRequest(
                prompt=prompt,
                model_name=self.model_name,
                max_output_tokens=self.max_output_tokens,
            )
        )
        patch_plan = parse_yaml_patch_plan(response.text)
        final_data = apply_yaml_patches(
            base_data=load_yaml_text(base_yaml),
            patches=patch_plan["patches"],
        )
        validation_errors = validate_final_lm_alert_yaml(final_data)
        final_yaml = dump_yaml_text(final_data)
        output_path = save_final_action_group_yaml(
            final_yaml=final_yaml,
            output_dir=output_dir,
        )
        return ActionGroupYamlCustomizationResult(
            questions=questions or (),
            patch_summary=patch_plan["summary"],
            patches=patch_plan["patches"],
            final_yaml=final_yaml,
            output_path=output_path,
            validation_passed=not validation_errors,
            validation_errors=validation_errors,
        )
