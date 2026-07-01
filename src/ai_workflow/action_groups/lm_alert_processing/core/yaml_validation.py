"""Post-patch YAML validation for LM Alert Processing."""

from typing import Any

from ai_workflow.action_groups.lm_alert_processing.config.constants import (
    ALLOWED_SNC_MAPPING_TARGETS,
    CREATE_INCIDENT_STEP_REQUIRED_LAST_OUTCOMES,
    FILTER_SCHEMA_NAME,
    FILTER_SCHEMA_VERSION,
    SERVICE_NOW_MAPPING_FIELDS,
    SNC_MAPPING_PATCH_STEP_NAMES,
    STEPS_WITHOUT_MAPPINGS,
    SUPPORTED_FILTER_OPERATORS,
)
from ai_workflow.action_groups.lm_alert_processing.helpers.yaml_helpers import (
    get_action_group,
)


def validate_final_lm_alert_yaml(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        action_group = get_action_group(data)
    except ValueError as error:
        return [str(error)]

    actions = action_group.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append("action_group.actions must be a non-empty list")
        return errors

    required_step_keys = (
        "_id",
        "name",
        "actionSpecificationId",
        "preconditionV2",
        "actionConfig",
        "mappings",
        "stopIf",
        "useAdditionalRecords",
    )
    for index, step in enumerate(actions, start=1):
        if not isinstance(step, dict):
            errors.append(f"actions[{index}] must be an object")
            continue
        for key in required_step_keys:
            if key not in step:
                errors.append(f"actions[{index}] missing {key}")
        errors.extend(_validate_step_shape(step=step, index=index))
        errors.extend(_validate_create_incident_precondition(step=step))

    return errors


def _validate_step_shape(step: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []

    precondition = step.get("preconditionV2")
    if precondition is not None:
        errors.extend(
            _validate_filter_condition(
                condition=precondition,
                path=f"actions[{index}].preconditionV2",
            )
        )

    action_config = step.get("actionConfig")
    if not isinstance(action_config, list):
        errors.append(f"actions[{index}].actionConfig must be a list")
    else:
        for config in action_config:
            if not isinstance(config, dict):
                errors.append(f"actions[{index}].actionConfig items must be objects")
                continue
            config_name = config.get("name")
            if config_name in SERVICE_NOW_MAPPING_FIELDS:
                errors.append(
                    f"actions[{index}].actionConfig contains mapped field {config_name}; use mappings instead"
                )

    mappings = step.get("mappings")
    if mappings is not None:
        if not isinstance(mappings, dict):
            errors.append(f"actions[{index}].mappings must be null or an object")
        else:
            step_name = step.get("name")
            if step_name in STEPS_WITHOUT_MAPPINGS:
                errors.append(
                    f"actions[{index}] ({step_name!r}) must not define mappings"
                )
            for target, target_mappings in mappings.items():
                if target not in ALLOWED_SNC_MAPPING_TARGETS and step_name in SNC_MAPPING_PATCH_STEP_NAMES:
                    errors.append(
                        f"actions[{index}].mappings.{target} is not an allowed "
                        "ServiceNow mapping field"
                    )
                if not isinstance(target_mappings, list):
                    errors.append(
                        f"actions[{index}].mappings.{target} must be a list"
                    )
                    continue
                for mapping in target_mappings:
                    if not isinstance(mapping, dict):
                        errors.append(
                            f"actions[{index}].mappings.{target} items must be objects"
                        )
                    condition = mapping.get("conditionV2") if isinstance(mapping, dict) else None
                    if condition is not None:
                        errors.extend(
                            _validate_filter_condition(
                                condition=condition,
                                path=f"actions[{index}].mappings.{target}.conditionV2",
                            )
                        )

    if not isinstance(step.get("stopIf"), list):
        errors.append(f"actions[{index}].stopIf must be a list")

    return errors


def _validate_filter_condition(condition: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(condition, dict):
        return [f"{path} must be an object"]

    if condition.get("schemaName") != FILTER_SCHEMA_NAME:
        errors.append(f"{path}.schemaName must be {FILTER_SCHEMA_NAME}")
    if condition.get("schemaVersion") != FILTER_SCHEMA_VERSION:
        errors.append(f"{path}.schemaVersion must be {FILTER_SCHEMA_VERSION}")

    expression = condition.get("expression")
    if not isinstance(expression, dict) or not expression:
        errors.append(f"{path}.expression must be a non-empty object")
        return errors

    return errors + _validate_filter_expression(expression, f"{path}.expression")


def _validate_filter_expression(expression: Any, path: str) -> list[str]:
    if not isinstance(expression, dict):
        return [f"{path} must be an object"]

    errors: list[str] = []
    for key, blocks in expression.items():
        if key in {"AND", "OR"}:
            if not isinstance(blocks, list):
                errors.append(f"{path}.{key} must be a list")
                continue
            for block_index, block in enumerate(blocks):
                errors.extend(
                    _validate_filter_expression(
                        expression=block,
                        path=f"{path}.{key}[{block_index}]",
                    )
                )
            continue

        if key not in SUPPORTED_FILTER_OPERATORS:
            errors.append(f"{path} has unsupported operator {key}")
            continue
        if not isinstance(blocks, list):
            errors.append(f"{path}.{key} must be a list")
            continue
        if key == "OLDER_THAN":
            errors.extend(_validate_older_than_operands(blocks, f"{path}.{key}"))

    return errors


def _validate_older_than_operands(operands: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(operands, list) or len(operands) != 2:
        return [f"{path} must be a list of two operands"]

    field_ref, duration_ref = operands[0], operands[1]
    if not isinstance(field_ref, dict) or "field" not in field_ref:
        errors.append(f"{path} field reference must be an object with field")
    elif field_ref.get("type") != "long":
        errors.append(f"{path} timestamp field must use type long")

    if not isinstance(duration_ref, dict):
        errors.append(f"{path} duration operand must be an object")
    elif "duration" not in duration_ref or "unit" not in duration_ref:
        errors.append(f"{path} duration operand must include duration and unit")

    return errors


def _validate_create_incident_precondition(step: dict[str, Any]) -> list[str]:
    step_name = step.get("name")
    if not isinstance(step_name, str):
        return []

    required_outcome = CREATE_INCIDENT_STEP_REQUIRED_LAST_OUTCOMES.get(step_name)
    if required_outcome is None:
        return []

    precondition = step.get("preconditionV2")
    expression = precondition.get("expression") if isinstance(precondition, dict) else None
    if _expression_includes_last_outcome(expression, required_outcome):
        return []

    return [
        f"Step {step_name!r} must require actionsystem.action.lastOutcome = "
        f"{required_outcome!r} before creating an incident"
    ]


def _expression_includes_last_outcome(
    expression: Any,
    expected_outcome: str,
) -> bool:
    if not isinstance(expression, dict):
        return False

    for key, blocks in expression.items():
        if key in {"AND", "OR"}:
            if isinstance(blocks, list):
                for block in blocks:
                    if _expression_includes_last_outcome(block, expected_outcome):
                        return True
            continue

        if key == "EQUALS" and isinstance(blocks, list) and len(blocks) >= 2:
            field_ref = blocks[0]
            value = blocks[1]
            if (
                isinstance(field_ref, dict)
                and field_ref.get("field") == "actionsystem.action.lastOutcome"
                and value == expected_outcome
            ):
                return True

    return False
