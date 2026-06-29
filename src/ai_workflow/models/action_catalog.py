"""Action Service catalog models used for Action Group validation."""

from dataclasses import dataclass, field
from typing import Any


class ActionCatalogValidationError(ValueError):
    """Raised when action catalog data is not valid."""


@dataclass(frozen=True)
class ActionConfigField:
    name: str
    type: str
    label: str | None = None
    default: Any = None
    has_default: bool = False
    required: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionConfigField":
        if not isinstance(data, dict):
            raise ActionCatalogValidationError("action config field must be an object")

        name = _required_string(data, "name", "action config field")
        field_type = _required_string(data, "type", f"action config field '{name}'")
        label = data.get("label")
        required = data.get("required", False)

        if label is not None and not isinstance(label, str):
            raise ActionCatalogValidationError(f"action config field '{name}' label must be a string")
        if not isinstance(required, bool):
            raise ActionCatalogValidationError(f"action config field '{name}' required must be a boolean")

        known_keys = {"name", "type", "label", "default", "required"}
        extra = {key: value for key, value in data.items() if key not in known_keys}

        return cls(
            name=name,
            type=field_type,
            label=label,
            default=data.get("default"),
            has_default="default" in data,
            required=required,
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
        }

        if self.label is not None:
            data["label"] = self.label
        if self.has_default:
            data["default"] = self.default
        if self.required:
            data["required"] = self.required
        data.update(self.extra)

        return data


@dataclass(frozen=True)
class ActionSpec:
    action_name: str
    action_id: str
    record_type: str
    outcomes: tuple[str, ...] = field(default_factory=tuple)
    action_config: tuple[ActionConfigField, ...] = field(default_factory=tuple)
    schema_version: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionSpec":
        if not isinstance(data, dict):
            raise ActionCatalogValidationError("action spec must be an object")

        action_name = _required_string(data, "action_name", "action spec")
        action_id = _required_string(data, "action_id", f"action spec '{action_name}'")
        record_type = _required_string(data, "record_type", f"action spec '{action_name}'")
        outcomes = _load_string_list(data.get("outcomes", []), f"action spec '{action_name}' outcomes")
        action_config = _load_action_config_fields(data.get("action_config", []))
        schema_version = data.get("schema_version")

        if schema_version is not None and not isinstance(schema_version, str):
            raise ActionCatalogValidationError(
                f"action spec '{action_name}' schema_version must be a string"
            )

        _ensure_unique_strings(outcomes, f"action spec '{action_name}' outcome")
        _ensure_unique_config_fields(action_config, action_name)

        known_keys = {
            "action_name",
            "action_id",
            "record_type",
            "outcomes",
            "action_config",
            "schema_version",
        }
        extra = {key: value for key, value in data.items() if key not in known_keys}

        return cls(
            action_name=action_name,
            action_id=action_id,
            record_type=record_type,
            outcomes=tuple(outcomes),
            action_config=tuple(action_config),
            schema_version=schema_version,
            extra=extra,
        )

    def config_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.action_config)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "action_name": self.action_name,
            "action_id": self.action_id,
            "record_type": self.record_type,
            "outcomes": list(self.outcomes),
            "action_config": [field.to_dict() for field in self.action_config],
        }
        if self.schema_version is not None:
            data["schema_version"] = self.schema_version
        data.update(self.extra)
        return data


@dataclass(frozen=True)
class ActionCatalog:
    actions: tuple[ActionSpec, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionCatalog":
        if not isinstance(data, dict):
            raise ActionCatalogValidationError("action catalog data must be an object")

        catalog_data = data.get("action_catalog", data)
        if not isinstance(catalog_data, dict):
            raise ActionCatalogValidationError("action_catalog must be an object")

        actions = _load_action_specs(catalog_data.get("actions"))
        _ensure_unique_action_names(actions)

        return cls(actions=tuple(actions))

    def action_names(self) -> tuple[str, ...]:
        return tuple(action.action_name for action in self.actions)

    def has_action(self, action_name: str) -> bool:
        return any(action.action_name == action_name for action in self.actions)

    def get_action(self, action_name: str) -> ActionSpec:
        for action in self.actions:
            if action.action_name == action_name:
                return action

        raise ActionCatalogValidationError(f"unknown action type: {action_name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_catalog": {
                "actions": [action.to_dict() for action in self.actions],
            }
        }


def _required_string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ActionCatalogValidationError(f"{label} requires non-empty string '{key}'")
    return value.strip()


def _load_string_list(raw_values: Any, label: str) -> list[str]:
    if raw_values is None:
        return []
    if not isinstance(raw_values, list):
        raise ActionCatalogValidationError(f"{label} must be a list")

    values: list[str] = []
    for value in raw_values:
        if not isinstance(value, str) or not value.strip():
            raise ActionCatalogValidationError(f"{label} must contain non-empty strings")
        values.append(value.strip())

    return values


def _load_action_specs(raw_actions: Any) -> list[ActionSpec]:
    if not isinstance(raw_actions, list) or not raw_actions:
        raise ActionCatalogValidationError("action catalog requires at least one action")

    return [ActionSpec.from_dict(action) for action in raw_actions]


def _load_action_config_fields(raw_fields: Any) -> list[ActionConfigField]:
    if raw_fields is None:
        return []
    if not isinstance(raw_fields, list):
        raise ActionCatalogValidationError("action_config must be a list")

    return [ActionConfigField.from_dict(field) for field in raw_fields]


def _ensure_unique_strings(values: list[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ActionCatalogValidationError(f"duplicate {label}: {value}")
        seen.add(value)


def _ensure_unique_action_names(actions: list[ActionSpec]) -> None:
    seen: set[str] = set()
    for action in actions:
        if action.action_name in seen:
            raise ActionCatalogValidationError(f"duplicate action name: {action.action_name}")
        seen.add(action.action_name)


def _ensure_unique_config_fields(fields: list[ActionConfigField], action_name: str) -> None:
    seen: set[str] = set()
    for field in fields:
        if field.name in seen:
            raise ActionCatalogValidationError(
                f"duplicate config field for action '{action_name}': {field.name}"
            )
        seen.add(field.name)
