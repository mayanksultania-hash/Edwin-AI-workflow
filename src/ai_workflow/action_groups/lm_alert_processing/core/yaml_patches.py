"""Apply declarative YAML patches to LM Alert Processing base workflow."""

from copy import deepcopy
from typing import Any

from ai_workflow.action_groups.lm_alert_processing.config.constants import (
    ALLOWED_SNC_MAPPING_TARGETS,
    CREATE_INCIDENT_STEP_REQUIRED_LAST_OUTCOMES,
    FILTER_SCHEMA_NAME,
    FILTER_SCHEMA_VERSION,
    OLDER_THAN_TIME_UNIT_SINGULAR,
    OLDER_THAN_TIME_UNITS,
    SERVICE_NOW_MAPPING_FIELDS,
    SNC_MAPPING_PATCH_STEP_NAMES,
    STEPS_WITHOUT_MAPPINGS,
    SUPPORTED_FILTER_OPERATORS,
)
from ai_workflow.action_groups.lm_alert_processing.helpers.yaml_helpers import (
    find_step,
    get_action_group,
    remove_step,
)


def apply_yaml_patches(
    base_data: dict[str, Any],
    patches: list[dict[str, Any]],
) -> dict[str, Any]:
    final_data = deepcopy(base_data)
    action_group = get_action_group(final_data)
    for patch in patches:
        patch_type = patch.get("type")
        if patch_type == "set_group_name":
            action_group["name"] = patch["value"]
        elif patch_type == "set_group_description":
            action_group["description"] = patch["value"]
        elif patch_type == "set_delay_seconds":
            step = find_step(action_group, patch["step_name"])
            _set_action_config_value(step, "delayTime", patch["value"])
        elif patch_type == "set_action_config_value":
            step = find_step(action_group, patch["step_name"])
            config_name = patch["config_name"]
            if config_name in SERVICE_NOW_MAPPING_FIELDS:
                _set_mapping_value(step, config_name, patch["value"])
            else:
                _set_action_config_value(step, config_name, patch["value"])
        elif patch_type == "set_mapping_value":
            step_name = patch["step_name"]
            target = patch["target"]
            _validate_mapping_patch(step_name=step_name, target=target)
            step = find_step(action_group, step_name)
            _set_mapping_value(step, target, patch["value"])
        elif patch_type == "set_step_precondition":
            step = find_step(action_group, patch["step_name"])
            conditions = _ensure_create_incident_precondition_conditions(
                step_name=patch["step_name"],
                conditions=patch.get("conditions", []),
            )
            step["preconditionV2"] = _build_filter_condition(
                combinator=patch.get("combinator", "AND"),
                conditions=conditions,
            )
        elif patch_type == "add_step_precondition_conditions":
            step = find_step(action_group, patch["step_name"])
            _add_precondition_conditions(
                step=step,
                combinator=patch.get("combinator", "AND"),
                conditions=patch.get("conditions", []),
            )
        elif patch_type == "remove_step":
            remove_step(action_group, patch["step_name"])
        else:
            raise ValueError(f"Unsupported patch type: {patch_type}")
    return final_data


def _validate_mapping_patch(step_name: str, target: str) -> None:
    if step_name in STEPS_WITHOUT_MAPPINGS:
        raise ValueError(
            f"set_mapping_value cannot target {step_name!r}; this step must keep mappings null"
        )
    if step_name not in SNC_MAPPING_PATCH_STEP_NAMES:
        raise ValueError(
            "set_mapping_value is only supported on Create or Update ServiceNow "
            f"Incident steps (got {step_name!r})"
        )
    if target not in ALLOWED_SNC_MAPPING_TARGETS:
        raise ValueError(
            f"set_mapping_value target {target!r} is not an allowed ServiceNow field"
        )


def _set_action_config_value(
    step: dict[str, Any],
    config_name: str,
    value: Any,
) -> None:
    configs = step.setdefault("actionConfig", [])
    if configs is None:
        configs = []
        step["actionConfig"] = configs

    for config in configs:
        if config.get("name") == config_name:
            config["value"] = value
            return

    configs.append(
        {
            "name": config_name,
            "type": _value_type(value),
            "value": value,
            "title": None,
            "description": None,
            "fieldType": _value_type(value),
            "validRecordTypes": None,
            "mandatory": False,
        }
    )


def _set_mapping_value(
    step: dict[str, Any],
    target: str,
    value: Any,
) -> None:
    mappings = step.setdefault("mappings", {})
    if mappings is None:
        mappings = {}
        step["mappings"] = mappings

    target_mappings = mappings.setdefault(target, [])
    for mapping in target_mappings:
        if mapping.get("type") == "value" and mapping.get("conditionV2") is None:
            mapping["mappedValue"] = value
            return

    for mapping in target_mappings:
        if mapping.get("type") == "value":
            mapping["mappedValue"] = value
            return

    target_mappings.append(
        {
            "type": "value",
            "conditionV2": None,
            "mappedValue": value,
            "mappedVariable": None,
            "mappedVariables": None,
            "format": None,
        }
    )


def _ensure_create_incident_precondition_conditions(
    step_name: str,
    conditions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    required_outcome = CREATE_INCIDENT_STEP_REQUIRED_LAST_OUTCOMES.get(step_name)
    if required_outcome is None:
        return conditions
    if _patch_conditions_include_last_outcome(conditions, required_outcome):
        return conditions
    return [
        {
            "field": "actionsystem.action.lastOutcome",
            "operator": "EQUALS",
            "value": required_outcome,
            "value_type": "string",
        },
        *conditions,
    ]


def _patch_conditions_include_last_outcome(
    conditions: list[dict[str, Any]],
    expected_outcome: str,
) -> bool:
    for condition in conditions:
        if (
            condition.get("field") == "actionsystem.action.lastOutcome"
            and str(condition.get("operator", "")).upper() == "EQUALS"
            and condition.get("value") == expected_outcome
        ):
            return True
    return False


def _build_filter_condition(
    combinator: str,
    conditions: list[dict[str, Any]],
) -> dict[str, Any]:
    operator_blocks = [_build_operator_block(condition) for condition in conditions]
    return {
        "schemaName": FILTER_SCHEMA_NAME,
        "schemaVersion": FILTER_SCHEMA_VERSION,
        "expression": {_normalize_combinator(combinator): operator_blocks},
    }


def _add_precondition_conditions(
    step: dict[str, Any],
    combinator: str,
    conditions: list[dict[str, Any]],
) -> None:
    precondition = step.get("preconditionV2")
    if not isinstance(precondition, dict) or not precondition.get("expression"):
        step["preconditionV2"] = _build_filter_condition(
            combinator=combinator,
            conditions=conditions,
        )
        return

    expression = precondition.setdefault("expression", {})
    combinator_key = _normalize_combinator(combinator)
    existing_blocks = expression.get(combinator_key)
    if not isinstance(existing_blocks, list):
        existing_blocks = []
        expression.clear()
        expression[combinator_key] = existing_blocks

    existing_blocks.extend(_build_operator_block(condition) for condition in conditions)


def _build_operator_block(condition: dict[str, Any]) -> dict[str, Any]:
    operator = str(condition["operator"]).upper()
    if operator not in SUPPORTED_FILTER_OPERATORS:
        raise ValueError(f"Unsupported condition operator: {operator}")

    if operator == "OLDER_THAN":
        return {
            operator: [
                {
                    "field": condition["field"],
                    "type": "long",
                },
                _build_older_than_duration_operand(condition),
            ]
        }

    value_type = condition.get("value_type", condition.get("type", "string"))
    return {
        operator: [
            {
                "field": condition["field"],
                "type": value_type,
            },
            condition.get("value"),
        ]
    }


def _build_older_than_duration_operand(condition: dict[str, Any]) -> dict[str, Any]:
    value = condition.get("value")
    value_type = str(condition.get("value_type", condition.get("type", "string"))).lower()

    if isinstance(value, dict) and "duration" in value and "unit" in value:
        return value

    if value_type in OLDER_THAN_TIME_UNITS:
        unit = OLDER_THAN_TIME_UNIT_SINGULAR.get(value_type, value_type)
        return {"duration": value, "unit": unit}

    raise ValueError(
        "OLDER_THAN conditions require value_type hour, minute, second, or day "
        f"(got {value_type!r})"
    )


def _normalize_combinator(combinator: str) -> str:
    normalized = str(combinator).upper()
    if normalized not in {"AND", "OR"}:
        raise ValueError(f"Unsupported condition combinator: {combinator}")
    return normalized


def _value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "string"
