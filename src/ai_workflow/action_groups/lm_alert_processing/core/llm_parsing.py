"""LLM response parsing for LM Alert Processing guided setup."""

from typing import Any

from pydantic import TypeAdapter

from ai_workflow.action_groups.common.action_schemas.base import (
    extract_group_id_from_question_key,
)
from ai_workflow.action_groups.lm_alert_processing.config.action_group import (
    build_lm_alert_action_group_step_groups,
)
from ai_workflow.action_groups.lm_alert_processing.core.llm_models import (
    GuidedQuestionModel,
    GuidedQuestionsOutputModel,
    YamlPatchPlanOutputModel,
)
from ai_workflow.action_groups.lm_alert_processing.helpers.llm_json_utils import (
    validate_llm_json,
)
from ai_workflow.models.action_group_customization import GuidedQuestion


def parse_guided_questions(text: str) -> tuple[GuidedQuestion, ...]:
    output = validate_llm_json(
        text=text,
        adapter=TypeAdapter(GuidedQuestionsOutputModel),
        label="guided questions",
    )
    _validate_guided_question_group_limits(output.questions)
    return tuple(
        GuidedQuestion(
            key=question.key,
            question=question.question,
            example_answer=question.example_answer,
        )
        for question in output.questions
    )


def _validate_guided_question_group_limits(
    questions: list[GuidedQuestionModel],
) -> None:
    group_ids = {group.group_id for group in build_lm_alert_action_group_step_groups()}
    counts: dict[str, int] = {}

    for question in questions:
        group_id = extract_group_id_from_question_key(question.key, group_ids)
        if group_id is None:
            continue

        counts[group_id] = counts.get(group_id, 0) + 1
        if counts[group_id] > 2:
            raise ValueError(
                "guided questions: at most 2 questions are allowed per step group "
                f"({group_id})"
            )


def parse_yaml_patch_plan(text: str) -> dict[str, Any]:
    output = validate_llm_json(
        text=text,
        adapter=TypeAdapter(YamlPatchPlanOutputModel),
        label="YAML patch plan",
    )
    return {
        "summary": output.summary,
        "patches": [
            patch.model_dump(mode="json")
            for patch in output.patches
        ],
    }
