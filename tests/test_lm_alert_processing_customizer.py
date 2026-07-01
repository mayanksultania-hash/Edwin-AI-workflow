from pathlib import Path
import asyncio
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.action_groups.lm_alert_processing import (
    LMAlertProcessingCustomizer,
    apply_yaml_patches,
    build_lm_alert_action_schema_prompt_context,
    build_lm_alert_processing_questions,
    build_lm_alert_step_group_prompt_context,
    build_lm_alert_step_groups,
    load_yaml_text,
    parse_guided_questions,
    parse_yaml_patch_plan,
    validate_final_lm_alert_yaml,
)
from ai_workflow.action_groups.lm_alert_processing.customizer import DEFAULT_BASE_YAML_PATH
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMResponse


class CapturingYamlLLMProvider(BaseLLMProvider):
    provider_name = "capturing-yaml"

    def __init__(self):
        self.prompts = []

    async def generate(self, request):
        self.prompts.append(request.prompt)
        if "LM Alert Processing question generation task." in request.prompt:
            text = json.dumps(
                {
                    "questions": [
                        {
                            "key": "incident_policy",
                            "question": "When should incidents be created?",
                            "example_answer": "Only for critical alerts.",
                        },
                        {
                            "key": "servicenow_fields",
                            "question": "Which ServiceNow fields should be mapped?",
                            "example_answer": "Assignment group is Network Operations.",
                        },
                        {
                            "key": "correlation_delay",
                            "question": "What delay should be used?",
                            "example_answer": "15 minutes.",
                        },
                        {
                            "key": "ai_investigation",
                            "question": "Should AI investigation run?",
                            "example_answer": "Yes, for critical alerts.",
                        },
                    ]
                }
            )
        else:
            text = json.dumps(
                {
                    "summary": "Set customer description, delay, mappings, and conditions.",
                    "patches": [
                        {
                            "type": "set_group_description",
                            "value": "Customer-specific LM Alert Processing",
                        },
                        {
                            "type": "set_delay_seconds",
                            "step_name": "Delay for 15 mins to allow new alerts to correlate",
                            "value": 900,
                        },
                        {
                            "type": "set_mapping_value",
                            "step_name": "Create ServiceNow Incident for this alert",
                            "target": "caller_id",
                            "value": "Edwin Integration",
                        },
                        {
                            "type": "set_mapping_value",
                            "step_name": "Update ServiceNow Incident linked to this alert",
                            "target": "resolved_by",
                            "value": "Edwin Integration",
                        },
                        {
                            "type": "add_step_precondition_conditions",
                            "step_name": "Create ServiceNow Incident for this alert",
                            "combinator": "AND",
                            "conditions": [
                                {
                                    "field": "alerts.alertDetails.currentSeverity",
                                    "operator": "GREATER_THAN_EQUAL",
                                    "value": 4,
                                    "value_type": "integer",
                                },
                                {
                                    "field": "alerts.alertDetails.workflowState",
                                    "operator": "EQUALS",
                                    "value": "incident-active",
                                    "value_type": "string",
                                },
                            ],
                        },
                    ],
                }
            )
        return LLMResponse(
            text=text,
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_build_lm_alert_processing_questions_returns_one_question_per_group():
    questions = build_lm_alert_processing_questions()

    assert len(questions) == 6
    assert questions[0].key == "alert_intake_path__sdt_handling"
    assert questions[-1].key == "auto_close_and_cleanup_path__delay_durations"
    assert all("__" in question.key for question in questions)


def test_default_lm_alert_base_yaml_path_points_to_project_inputs():
    assert DEFAULT_BASE_YAML_PATH == PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml"
    assert DEFAULT_BASE_YAML_PATH.exists()


def test_lm_alert_step_groups_cover_every_base_step_exactly_once():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    base_step_names = {
        step["name"] for step in base_data["action_group"]["actions"]
    }

    groups = build_lm_alert_step_groups()
    grouped_step_names = [
        step_name for group in groups for step_name in group.step_names
    ]

    assert grouped_step_names, "expected step groups to list steps"
    for step_name in grouped_step_names:
        assert step_name in base_step_names, f"unknown step in group: {step_name}"

    assert set(grouped_step_names) == base_step_names


def test_lm_alert_step_group_prompt_context_lists_groups_and_steps():
    context = build_lm_alert_step_group_prompt_context()

    assert "[alert_intake_path]" in context
    assert "[auto_close_and_cleanup_path]" in context
    assert "key: alert_intake_path__sdt_handling" in context
    assert "key: auto_close_and_cleanup_path__auto_close_rules" in context
    assert "Create ServiceNow Incident for this alert" in context
    assert "Delay for 15 mins to allow new alerts to correlate" in context


def test_parse_guided_questions_rejects_more_than_two_questions_per_group():
    payload = {
        "questions": [
            {
                "key": "alert_intake_path__sdt_handling",
                "question": "SDT?",
                "example_answer": "e.g. remove",
            },
            {
                "key": "alert_intake_path__alert_intake_rules",
                "question": "Intake rules?",
                "example_answer": "e.g. defaults",
            },
            {
                "key": "alert_intake_path__extra",
                "question": "Extra?",
                "example_answer": "e.g. no",
            },
        ]
    }

    try:
        parse_guided_questions(json.dumps(payload))
    except ValueError as exc:
        assert "at most 2 questions" in str(exc)
        assert "alert_intake_path" in str(exc)
    else:
        raise AssertionError("expected ValueError for too many questions in one group")


def test_lm_alert_action_schema_prompt_context_describes_reusable_action_ids():
    context = build_lm_alert_action_schema_prompt_context()

    assert "Update SNC Incident (update-snc-incident)" in context
    assert "Create SNC Incident (create-snc-incident)" in context
    assert "caller_id" in context
    assert "delayTime" in context
    assert "insights.ml.highestSeverity" in context
    assert "insights.insightDetails.workflowState" in context
    assert "insights.severity" not in context


def test_lm_alert_processing_customizer_generates_questions_from_base_yaml():
    customizer = LMAlertProcessingCustomizer(
        llm_provider=CapturingYamlLLMProvider(),
        model_name="test-model",
        base_yaml_path=PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml",
    )

    questions = asyncio.run(customizer.generate_questions_from_base_yaml())

    assert len(questions) == 4
    assert questions[0].key == "incident_policy"
    assert questions[0].question == "When should incidents be created?"
    assert "Reusable Action ID schemas" in customizer.llm_provider.prompts[-1]
    assert "Precondition fields" in customizer.llm_provider.prompts[-1]


def test_lm_alert_processing_customizer_customizes_base_yaml_and_saves_output():
    provider = CapturingYamlLLMProvider()
    customizer = LMAlertProcessingCustomizer(
        llm_provider=provider,
        model_name="test-model",
        base_yaml_path=PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml",
    )
    questions = asyncio.run(customizer.generate_questions_from_base_yaml())

    result = asyncio.run(
        customizer.customize_base_yaml(
            answers={
                "incident_policy": "Only for critical alerts.",
                "servicenow_fields": "Assignment group is Network Operations.",
                "correlation_delay": "15 minutes.",
                "ai_investigation": "Yes, for critical alerts.",
            },
            output_dir=PROJECT_ROOT / "outputs" / "tests",
            questions=questions,
        )
    )

    assert result.output_path.exists()
    assert result.output_path.name == "final.yaml"
    assert result.validation_passed is True
    assert result.patch_summary == "Set customer description, delay, mappings, and conditions."
    final_data = load_yaml_text(result.final_yaml)
    assert (
        final_data["action_group"]["description"]
        == "Customer-specific LM Alert Processing"
    )
    delay_step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"] == "Delay for 15 mins to allow new alerts to correlate"
    )
    assert delay_step["actionConfig"][0]["value"] == 900
    create_incident_step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this alert"
    )
    assert (
        create_incident_step["mappings"]["caller_id"][0]["mappedValue"]
        == "Edwin Integration"
    )
    assert all(
        config.get("name") != "caller_id"
        for config in create_incident_step["actionConfig"]
    )
    condition_blocks = create_incident_step["preconditionV2"]["expression"]["AND"]
    assert {
        "GREATER_THAN_EQUAL": [
            {"field": "alerts.alertDetails.currentSeverity", "type": "integer"},
            4,
        ]
    } in condition_blocks
    assert {
        "EQUALS": [
            {"field": "alerts.alertDetails.workflowState", "type": "string"},
            "incident-active",
        ]
    } in condition_blocks
    assert "Reusable Action ID schemas" in provider.prompts[-1]
    assert "Update SNC Incident (update-snc-incident)" in provider.prompts[-1]
    assert "caller_id" in provider.prompts[-1]
    assert "Workflow step groups" in provider.prompts[-1]
    assert "[alert_intake_path]" in provider.prompts[-1]


def test_apply_yaml_patches_can_replace_step_precondition():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_step_precondition",
                "step_name": "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago",
                "combinator": "AND",
                "conditions": [
                    {
                        "field": "alerts.alertDetails.currentSeverity",
                        "operator": "LESS_THAN_EQUAL",
                        "value": 2,
                        "value_type": "integer",
                    },
                    {
                        "field": "alerts.alertDetails.workflowState",
                        "operator": "EQUALS",
                        "value": "new",
                        "value_type": "string",
                    },
                ],
            }
        ],
    )

    step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"]
        == "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago"
    )
    assert step["preconditionV2"] == {
        "schemaName": "filterCondition",
        "schemaVersion": 4,
        "expression": {
            "AND": [
                {
                    "LESS_THAN_EQUAL": [
                        {
                            "field": "alerts.alertDetails.currentSeverity",
                            "type": "integer",
                        },
                        2,
                    ]
                },
                {
                    "EQUALS": [
                        {
                            "field": "alerts.alertDetails.workflowState",
                            "type": "string",
                        },
                        "new",
                    ]
                },
            ]
        },
    }


def test_apply_yaml_patches_rejects_unknown_patch_type():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    try:
        apply_yaml_patches(base_data=base_data, patches=[{"type": "bad_patch"}])
    except ValueError as error:
        assert "Unsupported patch type" in str(error)
    else:
        raise AssertionError("Expected unsupported patch type error")


def test_parse_yaml_patch_plan_accepts_add_step_precondition_conditions():
    plan = parse_yaml_patch_plan(
        json.dumps(
            {
                "summary": "Add incident creation conditions",
                "patches": [
                    {
                        "type": "add_step_precondition_conditions",
                        "step_name": "Create ServiceNow Incident for this alert",
                        "conditions": [
                            {
                                "field": "alerts.alertDetails.currentSeverity",
                                "operator": "GREATER_THAN_EQUAL",
                                "value": 4,
                                "value_type": "integer",
                            }
                        ],
                    }
                ],
            }
        )
    )

    assert plan["patches"][0]["type"] == "add_step_precondition_conditions"


def test_parse_yaml_patch_plan_rejects_unknown_patch_type_with_supported_list():
    try:
        parse_yaml_patch_plan(
            json.dumps(
                {
                    "summary": "Bad patch",
                    "patches": [{"type": "rewrite_everything"}],
                }
            )
        )
    except ValueError as error:
        assert "Invalid LLM YAML patch plan" in str(error)
        assert "rewrite_everything" in str(error)
        assert "add_step_precondition_conditions" in str(error)
    else:
        raise AssertionError("Expected unsupported patch type error")


def test_validate_final_lm_alert_yaml_rejects_mapped_field_in_action_config():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    step = next(
        step
        for step in base_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this alert"
    )
    step["actionConfig"].append({"name": "caller_id", "value": "Edwin Integration"})

    errors = validate_final_lm_alert_yaml(base_data)

    assert any("use mappings instead" in error for error in errors)


def test_apply_yaml_patches_builds_older_than_with_duration_and_unit():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_step_precondition",
                "step_name": "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago",
                "combinator": "AND",
                "conditions": [
                    {
                        "field": "alerts.meta.firstEventTimestamp",
                        "operator": "OLDER_THAN",
                        "value": 1,
                        "value_type": "hour",
                    }
                ],
            }
        ],
    )

    step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"]
        == "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago"
    )
    older_than = step["preconditionV2"]["expression"]["AND"][0]["OLDER_THAN"]
    assert older_than[0] == {
        "field": "alerts.meta.firstEventTimestamp",
        "type": "long",
    }
    assert older_than[1] == {"duration": 1, "unit": "hour"}


def test_validate_final_lm_alert_yaml_rejects_malformed_older_than():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    step = next(
        step
        for step in base_data["action_group"]["actions"]
        if step["name"]
        == "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago"
    )
    step["preconditionV2"]["expression"]["AND"].append(
        {
            "OLDER_THAN": [
                {"field": "alerts.meta.firstEventTimestamp", "type": "hour"},
                1,
            ]
        }
    )

    errors = validate_final_lm_alert_yaml(base_data)

    assert any("type long" in error for error in errors)
    assert any("duration operand" in error for error in errors)


def test_set_mapping_value_prefers_unconditional_mapping_entry():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_mapping_value",
                "step_name": "Create ServiceNow Incident for this alert",
                "target": "assignment_group",
                "value": "Network Operations",
            }
        ],
    )

    step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this alert"
    )
    assignment_group_mappings = step["mappings"]["assignment_group"]
    assert len(assignment_group_mappings) == 1
    assert assignment_group_mappings[0]["mappedValue"] == "Network Operations"
    assert assignment_group_mappings[0]["conditionV2"] is None

    resolved_by_mappings = step["mappings"]["resolved_by"]
    assert resolved_by_mappings[0]["conditionV2"] is not None
    assert resolved_by_mappings[0]["mappedValue"] == "Edwin Integration"


def test_set_step_precondition_on_create_alert_keeps_last_outcome_guard():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_step_precondition",
                "step_name": "Create ServiceNow Incident for this alert",
                "combinator": "AND",
                "conditions": [
                    {
                        "field": "alerts.alertDetails.currentSeverity",
                        "operator": "GREATER_THAN_EQUAL",
                        "value": 4,
                        "value_type": "integer",
                    },
                    {
                        "field": "alerts.alertDetails.workflowState",
                        "operator": "EQUALS",
                        "value": "incident-active",
                        "value_type": "string",
                    },
                ],
            }
        ],
    )

    step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this alert"
    )
    condition_blocks = step["preconditionV2"]["expression"]["AND"]
    assert {
        "EQUALS": [
            {"field": "actionsystem.action.lastOutcome", "type": "string"},
            "Alert updated",
        ]
    } in condition_blocks
    assert validate_final_lm_alert_yaml(final_data) == []


def test_set_step_precondition_on_create_insight_keeps_last_outcome_guard():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_step_precondition",
                "step_name": "Create ServiceNow Incident for this insight",
                "combinator": "AND",
                "conditions": [
                    {
                        "field": "insights.ml.highestSeverity",
                        "operator": "GREATER_THAN_EQUAL",
                        "value": 4,
                        "value_type": "integer",
                    },
                    {
                        "field": "insights.insightDetails.workflowState",
                        "operator": "EQUALS",
                        "value": "incident-active",
                        "value_type": "string",
                    },
                ],
            }
        ],
    )

    step = next(
        step
        for step in final_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this insight"
    )
    condition_blocks = step["preconditionV2"]["expression"]["AND"]
    assert {
        "EQUALS": [
            {"field": "actionsystem.action.lastOutcome", "type": "string"},
            "Insight updated",
        ]
    } in condition_blocks
    assert validate_final_lm_alert_yaml(final_data) == []


def test_validate_final_lm_alert_yaml_rejects_create_incident_missing_last_outcome():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    step = next(
        step
        for step in base_data["action_group"]["actions"]
        if step["name"] == "Create ServiceNow Incident for this alert"
    )
    step["preconditionV2"] = {
        "schemaName": "filterCondition",
        "schemaVersion": 4,
        "expression": {
            "AND": [
                {
                    "EQUALS": [
                        {
                            "field": "alerts.alertDetails.workflowState",
                            "type": "string",
                        },
                        "incident-active",
                    ]
                }
            ]
        },
    }

    errors = validate_final_lm_alert_yaml(base_data)

    assert any("lastOutcome = 'Alert updated'" in error for error in errors)


def test_apply_yaml_patches_rejects_mapping_on_find_reference_step():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    try:
        apply_yaml_patches(
            base_data=base_data,
            patches=[
                {
                    "type": "set_mapping_value",
                    "step_name": "Find a LM-DX reference for this alert",
                    "target": "dummy_field",
                    "value": "skip",
                }
            ],
        )
    except ValueError as error:
        assert "must keep mappings null" in str(error)
    else:
        raise AssertionError("expected mapping patch on find step to be rejected")


def test_apply_yaml_patches_rejects_unknown_mapping_target():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    try:
        apply_yaml_patches(
            base_data=base_data,
            patches=[
                {
                    "type": "set_mapping_value",
                    "step_name": "Update ServiceNow Incident linked to this alert",
                    "target": "dummy_field",
                    "value": "skip",
                }
            ],
        )
    except ValueError as error:
        assert "not an allowed ServiceNow field" in str(error)
    else:
        raise AssertionError("expected unknown mapping target to be rejected")


def test_validate_final_lm_alert_yaml_rejects_mappings_on_find_reference_step():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    step = next(
        step
        for step in base_data["action_group"]["actions"]
        if step["name"] == "Find a LM-DX reference for this alert"
    )
    step["mappings"] = {
        "dummy_field": [
            {
                "type": "value",
                "conditionV2": None,
                "mappedValue": "skip",
                "mappedVariable": None,
                "mappedVariables": None,
                "format": None,
            }
        ]
    }

    errors = validate_final_lm_alert_yaml(base_data)

    assert any("must not define mappings" in error for error in errors)


def test_set_step_precondition_replaces_auto_close_conditions_without_duplicates():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    step_name = (
        "Auto-close alerts that are not valid for ticketing and created more than 1 hour ago"
    )
    original_step = next(
        step for step in base_data["action_group"]["actions"] if step["name"] == step_name
    )
    original_condition_count = len(
        original_step["preconditionV2"]["expression"]["AND"]
    )

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "set_step_precondition",
                "step_name": step_name,
                "combinator": "AND",
                "conditions": [
                    {
                        "field": "alerts.alertDetails.workflowState",
                        "operator": "EQUALS",
                        "value": "new",
                        "value_type": "string",
                    },
                    {
                        "field": "alerts.alertDetails.worstSeverity",
                        "operator": "LESS_THAN_EQUAL",
                        "value": 2,
                        "value_type": "integer",
                    },
                    {
                        "field": "actionsystem.action.lastOutcome",
                        "operator": "EQUALS",
                        "value": "Delay Completed",
                        "value_type": "string",
                    },
                    {
                        "field": "alerts.meta.firstEventTimestamp",
                        "operator": "OLDER_THAN",
                        "value": 1,
                        "value_type": "hour",
                    },
                ],
            }
        ],
    )

    step = next(
        step for step in final_data["action_group"]["actions"] if step["name"] == step_name
    )
    conditions = step["preconditionV2"]["expression"]["AND"]
    assert len(conditions) == 4
    assert len(conditions) != original_condition_count * 2
    assert conditions[-1]["OLDER_THAN"][1] == {"duration": 1, "unit": "hour"}


def test_parse_yaml_patch_plan_accepts_remove_step():
    plan = parse_yaml_patch_plan(
        json.dumps(
            {
                "summary": "Remove unused AI summarise step",
                "patches": [
                    {
                        "type": "remove_step",
                        "step_name": "Summarise insights with AI",
                    }
                ],
            }
        )
    )

    assert plan["patches"][0]["type"] == "remove_step"
    assert plan["patches"][0]["step_name"] == "Summarise insights with AI"


def test_apply_yaml_patches_can_remove_step_by_name():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    original_count = len(base_data["action_group"]["actions"])

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[
            {
                "type": "remove_step",
                "step_name": "Summarise insights with AI",
            }
        ],
    )

    step_names = [step["name"] for step in final_data["action_group"]["actions"]]
    assert "Summarise insights with AI" not in step_names
    assert len(step_names) == original_count - 1
    assert not validate_final_lm_alert_yaml(final_data)


def test_apply_yaml_patches_remove_step_only_removes_first_duplicate_name():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )
    duplicate_name = "Store a reference to the SNC incident request"
    original_matches = sum(
        1
        for step in base_data["action_group"]["actions"]
        if step["name"] == duplicate_name
    )
    assert original_matches == 2

    final_data = apply_yaml_patches(
        base_data=base_data,
        patches=[{"type": "remove_step", "step_name": duplicate_name}],
    )

    remaining_matches = sum(
        1
        for step in final_data["action_group"]["actions"]
        if step["name"] == duplicate_name
    )
    assert remaining_matches == 1


def test_apply_yaml_patches_rejects_removing_unknown_step():
    base_data = load_yaml_text(
        (PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml").read_text(
            encoding="utf-8"
        )
    )

    try:
        apply_yaml_patches(
            base_data=base_data,
            patches=[{"type": "remove_step", "step_name": "Step that does not exist"}],
        )
    except ValueError as error:
        assert "Step not found" in str(error)
    else:
        raise AssertionError("Expected missing step error")


def test_apply_yaml_patches_rejects_removing_last_step():
    base_data = {
        "action_group": {
            "actions": [
                {
                    "_id": "only-step",
                    "name": "Only step",
                    "actionSpecificationId": "test",
                    "preconditionV2": None,
                    "actionConfig": [],
                    "mappings": None,
                    "stopIf": [],
                    "useAdditionalRecords": None,
                }
            ]
        }
    }

    try:
        apply_yaml_patches(
            base_data=base_data,
            patches=[{"type": "remove_step", "step_name": "Only step"}],
        )
    except ValueError as error:
        assert "Cannot remove the last workflow step" in str(error)
    else:
        raise AssertionError("Expected last step removal error")
