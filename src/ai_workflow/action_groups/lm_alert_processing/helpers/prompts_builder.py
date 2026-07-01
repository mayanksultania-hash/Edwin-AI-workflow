"""Jinja prompt builders for LM Alert Processing customization."""

from ai_workflow.action_groups.lm_alert_processing.config.action_ids import (
    build_lm_alert_action_id_prompt_context,
)
from ai_workflow.action_groups.lm_alert_processing.config.action_group import (
    build_lm_alert_action_group_step_group_prompt_context,
)
from ai_workflow.prompting.template_renderer import render_prompt_template


def build_lm_alert_question_generation_prompt(base_yaml: str) -> str:
    return render_prompt_template(
        "action_groups/lm_alert_processing/prompts/question_generation.j2",
        {
            "action_schema_context": build_lm_alert_action_id_prompt_context(),
            "step_group_context": build_lm_alert_action_group_step_group_prompt_context(),
            "base_yaml": base_yaml,
        },
    )


def build_lm_alert_yaml_patch_prompt(
    base_yaml: str,
    answers: dict[str, str],
) -> str:
    return render_prompt_template(
        "action_groups/lm_alert_processing/prompts/yaml_patch_generation.j2",
        {
            "action_schema_context": build_lm_alert_action_id_prompt_context(),
            "step_group_context": build_lm_alert_action_group_step_group_prompt_context(),
            "answers": answers,
            "base_yaml": base_yaml,
        },
    )
