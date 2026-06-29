"""Action Group models used for Phase 2 Action Service YAML."""

from dataclasses import dataclass, field
from typing import Any


class ActionGroupValidationError(ValueError):
    """Raised when action group data is not valid."""


@dataclass(frozen=True)
class ConditionItem:
    record: str
    field: str
    operator: str
    value: Any = None
    has_value: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConditionItem":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("condition must be an object")

        record = _required_string(data, "record", "condition")
        field_name = _required_string(data, "field", "condition")
        operator = _required_string(data, "operator", "condition")

        return cls(
            record=record,
            field=field_name,
            operator=operator,
            value=data.get("value"),
            has_value="value" in data,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "record": self.record,
            "field": self.field,
            "operator": self.operator,
        }
        if self.has_value:
            data["value"] = self.value
        return data


@dataclass(frozen=True)
class ConditionGroup:
    operator: str
    conditions: tuple[ConditionItem, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConditionGroup":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("condition group must be an object")

        operator = _required_string(data, "operator", "condition group")
        conditions = _load_condition_items(data.get("conditions"))

        return cls(operator=operator, conditions=tuple(conditions))

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "conditions": [condition.to_dict() for condition in self.conditions],
        }


@dataclass(frozen=True)
class MappingValue:
    type: str
    value: Any = None
    format: str | None = None
    variables: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    only_when: ConditionGroup | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MappingValue":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("mapping value must be an object")

        mapping_type = _required_string(data, "type", "mapping value")
        only_when = _optional_condition_group(data.get("only_when"))
        variables = data.get("variables", [])

        if variables is None:
            variables = []
        if not isinstance(variables, list):
            raise ActionGroupValidationError("mapping value variables must be a list")
        for variable in variables:
            if not isinstance(variable, dict):
                raise ActionGroupValidationError("mapping value variable must be an object")

        known_keys = {"type", "value", "format", "variables", "only_when"}
        extra = {key: value for key, value in data.items() if key not in known_keys}

        return cls(
            type=mapping_type,
            value=data.get("value"),
            format=data.get("format"),
            variables=tuple(dict(variable) for variable in variables),
            only_when=only_when,
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type}
        data.update(self.extra)

        if self.value is not None:
            data["value"] = self.value
        if self.format is not None:
            data["format"] = self.format
        if self.variables:
            data["variables"] = [dict(variable) for variable in self.variables]
        if self.only_when is not None:
            data["only_when"] = self.only_when.to_dict()

        return data


@dataclass(frozen=True)
class MappedField:
    target: str
    mappings: tuple[MappingValue, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MappedField":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("mapped field must be an object")

        target = _required_string(data, "target", "mapped field")
        mappings = _load_mapping_values(data.get("mappings"))

        return cls(target=target, mappings=tuple(mappings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "mappings": [mapping.to_dict() for mapping in self.mappings],
        }


@dataclass(frozen=True)
class ActionStep:
    order: int
    id: str
    action_type: str
    name: str
    description: str
    start_condition: ConditionGroup | None = None
    stop_condition: ConditionGroup | None = None
    config: dict[str, Any] = field(default_factory=dict)
    mapped_fields: tuple[MappedField, ...] = field(default_factory=tuple)
    use_additional_records: bool | None = None
    preload: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionStep":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("action step must be an object")

        order = _required_int(data, "order", "action step")
        step_id = _required_string(data, "id", "action step")
        action_type = _required_string(data, "action_type", f"action step '{step_id}'")
        name = _required_string(data, "name", f"action step '{step_id}'")
        description = _required_string(data, "description", f"action step '{step_id}'")
        config = data.get("config", {})

        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise ActionGroupValidationError(f"action step '{step_id}' config must be an object")

        return cls(
            order=order,
            id=step_id,
            action_type=action_type,
            name=name,
            description=description,
            start_condition=_optional_condition_group(data.get("start_condition")),
            stop_condition=_optional_condition_group(data.get("stop_condition")),
            config=config,
            mapped_fields=tuple(_load_mapped_fields(data.get("mapped_fields", []))),
            use_additional_records=data.get("use_additional_records"),
            preload=data.get("preload"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "order": self.order,
            "id": self.id,
            "action_type": self.action_type,
            "name": self.name,
            "description": self.description,
        }

        if self.start_condition is not None:
            data["start_condition"] = self.start_condition.to_dict()
        if self.stop_condition is not None:
            data["stop_condition"] = self.stop_condition.to_dict()
        if self.config:
            data["config"] = self.config
        if self.mapped_fields:
            data["mapped_fields"] = [mapped_field.to_dict() for mapped_field in self.mapped_fields]
        if self.use_additional_records is not None:
            data["use_additional_records"] = self.use_additional_records
        if self.preload is not None:
            data["preload"] = self.preload

        return data


@dataclass(frozen=True)
class ActionGroup:
    name: str
    description: str
    source: str
    rule: str | None
    steps: tuple[ActionStep, ...]
    group_condition: ConditionGroup | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionGroup":
        if not isinstance(data, dict):
            raise ActionGroupValidationError("action group data must be an object")

        action_group_data = data.get("action_group", data)
        if not isinstance(action_group_data, dict):
            raise ActionGroupValidationError("action_group must be an object")

        name = _required_string(action_group_data, "name", "action group")
        description = _required_string(action_group_data, "description", "action group")
        source = _required_string(action_group_data, "source", "action group")
        rule = action_group_data.get("rule")
        steps = _load_steps(action_group_data.get("steps"))

        _ensure_unique_step_ids(steps)
        _ensure_unique_step_orders(steps)

        if rule is not None and not isinstance(rule, str):
            raise ActionGroupValidationError("action group rule must be a string or null")

        return cls(
            name=name,
            description=description,
            source=source,
            rule=rule,
            steps=tuple(steps),
            group_condition=_optional_condition_group(action_group_data.get("group_condition")),
        )

    def to_dict(self) -> dict[str, Any]:
        action_group_data: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "rule": self.rule,
        }

        if self.group_condition is not None:
            action_group_data["group_condition"] = self.group_condition.to_dict()

        action_group_data["steps"] = [step.to_dict() for step in self.steps]

        return {"action_group": action_group_data}


def _required_string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ActionGroupValidationError(f"{label} requires non-empty string '{key}'")
    return value.strip()


def _required_int(data: dict[str, Any], key: str, label: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ActionGroupValidationError(f"{label} requires integer '{key}'")
    return value


def _load_steps(raw_steps: Any) -> list[ActionStep]:
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ActionGroupValidationError("action group requires at least one step")
    return [ActionStep.from_dict(step) for step in raw_steps]


def _load_condition_items(raw_conditions: Any) -> list[ConditionItem]:
    if not isinstance(raw_conditions, list) or not raw_conditions:
        raise ActionGroupValidationError("condition group requires at least one condition")
    return [ConditionItem.from_dict(condition) for condition in raw_conditions]


def _load_mapping_values(raw_mappings: Any) -> list[MappingValue]:
    if not isinstance(raw_mappings, list) or not raw_mappings:
        raise ActionGroupValidationError("mapped field requires at least one mapping")
    return [MappingValue.from_dict(mapping) for mapping in raw_mappings]


def _load_mapped_fields(raw_mapped_fields: Any) -> list[MappedField]:
    if raw_mapped_fields is None:
        return []
    if not isinstance(raw_mapped_fields, list):
        raise ActionGroupValidationError("mapped_fields must be a list")
    return [MappedField.from_dict(mapped_field) for mapped_field in raw_mapped_fields]


def _optional_condition_group(raw_condition_group: Any) -> ConditionGroup | None:
    if raw_condition_group is None:
        return None
    return ConditionGroup.from_dict(raw_condition_group)


def _ensure_unique_step_ids(steps: list[ActionStep]) -> None:
    seen: set[str] = set()
    for step in steps:
        if step.id in seen:
            raise ActionGroupValidationError(f"duplicate step id: {step.id}")
        seen.add(step.id)


def _ensure_unique_step_orders(steps: list[ActionStep]) -> None:
    seen: set[int] = set()
    for step in steps:
        if step.order in seen:
            raise ActionGroupValidationError(f"duplicate step order: {step.order}")
        seen.add(step.order)
