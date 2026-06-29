"""Compile intermediate Action Group YAML models into Action Service JSON."""

from typing import Any

from ai_workflow.models.action_catalog import ActionCatalog, ActionConfigField, ActionSpec
from ai_workflow.models.action_group import (
    ActionGroup,
    ActionStep,
    ConditionGroup,
    ConditionItem,
    MappedField,
    MappingValue,
)


ACTION_GROUP_SCHEMA_VERSION = "20161209.01"
FILTER_SCHEMA_VERSION = "4"


def compile_action_group_to_action_service_json(
    action_group: ActionGroup,
    catalog: ActionCatalog,
) -> dict[str, Any]:
    """Compile an Action Group into the JSON shape used by Action Service."""

    compiled: dict[str, Any] = {
        "schemaType": "action_group",
        "schemaVersion": ACTION_GROUP_SCHEMA_VERSION,
        "name": action_group.name,
        "description": action_group.description,
        "inputType": action_group.source,
    }

    if action_group.group_condition is not None:
        compiled["uiCondition"] = _compile_condition_group(action_group.group_condition)

    compiled["actions"] = [
        _compile_step(step=step, action_spec=catalog.get_action(step.action_type))
        for step in sorted(action_group.steps, key=lambda item: item.order)
    ]

    return compiled


def _compile_step(step: ActionStep, action_spec: ActionSpec) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "schemaType": "action_group_entry",
        "schemaVersion": _entry_schema_version(action_spec),
        "actionSpecification": _compile_action_specification(step, action_spec),
    }

    action_config = _compile_step_action_config(step.config, action_spec.action_config)
    if action_config:
        entry["actionConfig"] = action_config

    if step.preload is not None:
        entry["preload"] = step.preload

    mappings = _compile_mappings(step.mapped_fields)
    if mappings:
        entry["mappings"] = mappings

    stop_if = _compile_stop_if(step.stop_condition)
    entry["stopIf"] = stop_if

    if step.start_condition is not None:
        entry["preconditionV2"] = _compile_condition_group(step.start_condition)

    if step.use_additional_records is not None:
        entry["useAdditionalRecords"] = step.use_additional_records

    if step.name:
        entry["name"] = step.name
    if step.description:
        entry["description"] = step.description

    return entry


def _compile_action_specification(
    step: ActionStep,
    action_spec: ActionSpec,
) -> dict[str, Any]:
    compiled = {
        "schemaType": "action_spec",
        "schemaVersion": action_spec.schema_version or ACTION_GROUP_SCHEMA_VERSION,
        "actionName": action_spec.action_name,
        "actionId": action_spec.action_id,
        "recordType": action_spec.record_type,
        "actionConfig": _compile_action_config({}, action_spec.action_config),
        "outcomes": list(action_spec.outcomes),
    }
    compiled.update(action_spec.extra)
    return compiled


def _compile_action_config(
    step_config: dict[str, Any],
    catalog_config: tuple[ActionConfigField, ...],
) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []

    for field in catalog_config:
        if field.name in step_config:
            value = step_config[field.name]
        elif field.has_default:
            value = field.default
        elif "value" in field.extra:
            value = field.extra["value"]
        else:
            value = None

        item = _compile_config_field(field)
        if value is not None:
            item["value"] = value
        compiled.append(item)

    return compiled


def _compile_step_action_config(
    step_config: dict[str, Any],
    catalog_config: tuple[ActionConfigField, ...],
) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    catalog_fields = {field.name: field for field in catalog_config}

    for name, value in step_config.items():
        field = catalog_fields.get(name)
        item: dict[str, Any] = {
            "name": name,
            "value": value,
        }
        if field is not None and not field.extra:
            item["type"] = field.type
        compiled.append(item)

    return compiled


def _compile_config_field(field: ActionConfigField) -> dict[str, Any]:
    item: dict[str, Any] = {"name": field.name}
    for key in ("description", "title", "fieldType"):
        if key in field.extra:
            item[key] = field.extra[key]
    item["type"] = field.type
    return item


def _entry_schema_version(action_spec: ActionSpec) -> str:
    if action_spec.extra.get("supportsMultipleRecords") is True:
        return "20201023.01"
    return ACTION_GROUP_SCHEMA_VERSION


def _compile_mappings(mapped_fields: tuple[MappedField, ...]) -> dict[str, list[dict[str, Any]]]:
    compiled: dict[str, list[dict[str, Any]]] = {}

    for mapped_field in mapped_fields:
        compiled[mapped_field.target] = [
            _compile_mapping_value(mapping) for mapping in mapped_field.mappings
        ]

    return compiled


def _compile_mapping_value(mapping: MappingValue) -> dict[str, Any]:
    if mapping.type == "value":
        return _with_mapping_condition(
            mapping,
            {
                "type": "value",
                "mappedValue": mapping.value,
            },
        )

    if mapping.type == "variable":
        return _with_mapping_condition(
            mapping,
            {
                "type": "variable",
                "mappedVariable": _mapping_variable(mapping),
            },
        )

    if mapping.type == "multi_variable":
        return _with_mapping_condition(
            mapping,
            {
                "type": "multi_variable",
                "format": mapping.format,
                "mappedVariables": [_variable_value(variable) for variable in mapping.variables],
            },
        )

    if mapping.type == "increment_value":
        compiled = {"type": "increment_value"}
        if mapping.value is not None:
            compiled["incrementVariable"] = mapping.value
        elif "incrementVariable" in mapping.extra:
            compiled["incrementVariable"] = mapping.extra["incrementVariable"]
        return _with_mapping_condition(mapping, compiled)

    compiled = {"type": mapping.type}
    compiled.update(mapping.extra)
    if mapping.value is not None:
        compiled["value"] = mapping.value
    return _with_mapping_condition(mapping, compiled)


def _with_mapping_condition(mapping: MappingValue, compiled: dict[str, Any]) -> dict[str, Any]:
    if mapping.only_when is not None:
        compiled["conditionV2"] = _compile_condition_group(mapping.only_when)
    return compiled


def _mapping_variable(mapping: MappingValue) -> Any:
    if "mappedVariable" in mapping.extra:
        return mapping.extra["mappedVariable"]
    if mapping.value is not None:
        return mapping.value
    if mapping.variables:
        return _variable_value(mapping.variables[0])
    return None


def _variable_value(variable: dict[str, Any]) -> Any:
    return (
        variable.get("value")
        or variable.get("path")
        or variable.get("field")
        or variable.get("mappedVariable")
    )


def _compile_stop_if(stop_condition: ConditionGroup | None) -> list[str]:
    if stop_condition is None:
        return []

    values: list[str] = []
    for condition in stop_condition.conditions:
        if isinstance(condition.value, str):
            values.append(condition.value)
    return values


def _compile_condition_group(condition_group: ConditionGroup) -> dict[str, Any]:
    expression = _compile_condition_group_expression(condition_group)

    return {
        "schemaName": "filterCondition",
        "schemaVersion": FILTER_SCHEMA_VERSION,
        "expression": expression,
    }


def _compile_condition_group_expression(condition_group: ConditionGroup) -> dict[str, Any]:
    if condition_group.operator in {"AND", "OR"}:
        return {
            condition_group.operator: [
                _compile_condition_item(condition)
                for condition in condition_group.conditions
            ]
        }

    if len(condition_group.conditions) != 1:
        return {
            condition_group.operator: [
                _compile_condition_item(condition)
                for condition in condition_group.conditions
            ]
        }

    return _compile_condition_item(condition_group.conditions[0])


def _compile_condition_item(condition: ConditionItem) -> dict[str, Any]:
    expression_value: list[Any] = [
        {
            "field": _condition_field(condition),
            "type": _condition_value_type(condition.value),
        }
    ]
    if condition.has_value:
        expression_value.append(condition.value)

    return {condition.operator: expression_value}


def _condition_field(condition: ConditionItem) -> str:
    if condition.field.startswith(f"{condition.record}."):
        return condition.field

    return f"{condition.record}.{condition.field}"


def _condition_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"
