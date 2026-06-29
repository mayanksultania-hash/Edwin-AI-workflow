"""Validate Action Groups against Action UI catalog context."""

from dataclasses import dataclass
from typing import Iterable

from ai_workflow.mcp.action_ui_context import ActionUiContext
from ai_workflow.models.action_catalog import ActionCatalog, ActionSpec
from ai_workflow.models.action_field_catalog import ActionFieldCatalog
from ai_workflow.models.action_group import (
    ActionGroup,
    ActionStep,
    ConditionGroup,
    ConditionItem,
    MappingValue,
)


class ActionGroupValidatorError(ValueError):
    """Raised when an Action Group is not valid for the Action UI catalog."""


@dataclass(frozen=True)
class ActionGroupValidator:
    catalog: ActionCatalog
    source_types: tuple[str, ...]
    condition_operators: tuple[str, ...]
    mapping_types: tuple[str, ...]
    field_catalog: ActionFieldCatalog | None = None

    @classmethod
    def from_context(cls, context: ActionUiContext) -> "ActionGroupValidator":
        return cls(
            catalog=context.catalog,
            source_types=context.source_types,
            condition_operators=context.condition_operator_keys,
            mapping_types=context.mapping_types,
            field_catalog=context.field_catalog,
        )

    def validate(self, action_group: ActionGroup) -> None:
        self._validate_general(action_group)
        self._validate_group_condition(action_group)
        self._validate_actions(action_group)

    def _validate_general(self, action_group: ActionGroup) -> None:
        if action_group.source not in self.source_types:
            raise ActionGroupValidatorError(
                f"General source '{action_group.source}' is not a valid Action UI source"
            )

    def _validate_actions(self, action_group: ActionGroup) -> None:
        for step in action_group.steps:
            action_spec = self._get_action_spec(step)
            self._validate_start_condition(step)
            self._validate_stop_condition(step, action_spec)
            self._validate_action_config(step, action_spec)
            self._validate_mapped_fields(step, action_spec)
            self._validate_preload(step)

    def _get_action_spec(self, step: ActionStep) -> ActionSpec:
        try:
            return self.catalog.get_action(step.action_type)
        except ValueError as error:
            raise ActionGroupValidatorError(
                f"Action #{step.order} '{step.name}' uses unknown action type "
                f"'{step.action_type}'"
            ) from error

    def _validate_group_condition(self, action_group: ActionGroup) -> None:
        if action_group.group_condition is None:
            return

        self._validate_condition_group(
            condition_group=action_group.group_condition,
            ui_section="Group condition",
            step=None,
        )

    def _validate_start_condition(self, step: ActionStep) -> None:
        if step.start_condition is None:
            return

        self._validate_condition_group(
            condition_group=step.start_condition,
            ui_section="Start Condition",
            step=step,
        )

    def _validate_stop_condition(self, step: ActionStep, action_spec: ActionSpec) -> None:
        if step.stop_condition is None:
            return

        self._validate_condition_group(
            condition_group=step.stop_condition,
            ui_section="Stop condition",
            step=step,
        )

        for outcome in _condition_values(step.stop_condition):
            if outcome not in action_spec.outcomes:
                raise ActionGroupValidatorError(
                    f"Action #{step.order} '{step.name}' has unknown Stop condition outcome "
                    f"'{outcome}' for action type '{step.action_type}'"
                )

    def _validate_action_config(self, step: ActionStep, action_spec: ActionSpec) -> None:
        allowed_config_names = set(action_spec.config_field_names())
        required_config_names = {
            config.name for config in action_spec.action_config if config.required
        }
        provided_config_names = set(step.config)

        for config_name in provided_config_names:
            if config_name not in allowed_config_names:
                raise ActionGroupValidatorError(
                    f"Action #{step.order} '{step.name}' has unknown Action Config "
                    f"'{config_name}' for action type '{step.action_type}'"
                )

        for config_name in required_config_names:
            if config_name not in provided_config_names:
                raise ActionGroupValidatorError(
                    f"Action #{step.order} '{step.name}' is missing required Action Config "
                    f"'{config_name}' for action type '{step.action_type}'"
                )

    def _validate_mapped_fields(self, step: ActionStep, action_spec: ActionSpec) -> None:
        for mapped_field in step.mapped_fields:
            self._validate_field_path(
                field_path=_mapped_target_path(mapped_field.target, action_spec.record_type),
                ui_section="Mapped Fields target",
                owner=_condition_owner(step),
            )
            for mapping in mapped_field.mappings:
                self._validate_mapping_value(mapping, step)

    def _validate_mapping_value(self, mapping: MappingValue, step: ActionStep) -> None:
        if mapping.type not in self.mapping_types:
            raise ActionGroupValidatorError(
                f"Action #{step.order} '{step.name}' has unknown Mapped Fields type "
                f"'{mapping.type}'"
            )

        if mapping.only_when is not None:
            self._validate_condition_group(
                condition_group=mapping.only_when,
                ui_section="Mapped Fields Only When",
                step=step,
            )

        for field_path in _mapping_field_paths(mapping):
            self._validate_field_path(
                field_path=field_path,
                ui_section="Mapped Fields variable",
                owner=_condition_owner(step),
            )

    def _validate_preload(self, step: ActionStep) -> None:
        if step.preload is None:
            return

        if step.preload not in self.source_types:
            raise ActionGroupValidatorError(
                f"Action #{step.order} '{step.name}' has invalid preload "
                f"record type '{step.preload}'"
            )

    def _validate_condition_group(
        self,
        condition_group: ConditionGroup,
        ui_section: str,
        step: ActionStep | None,
    ) -> None:
        if (
            condition_group.operator not in {"AND", "OR"}
            and condition_group.operator not in self.condition_operators
        ):
            raise ActionGroupValidatorError(
                f"{_condition_owner(step)} has unknown {ui_section} group "
                f"operator '{condition_group.operator}'"
            )

        for condition in condition_group.conditions:
            if condition.operator not in self.condition_operators:
                raise ActionGroupValidatorError(
                    f"{_condition_owner(step)} has unknown {ui_section} "
                    f"operator '{condition.operator}'"
                )
            self._validate_condition_field(condition, ui_section, step)

    def _validate_condition_field(
        self,
        condition: ConditionItem,
        ui_section: str,
        step: ActionStep | None,
    ) -> None:
        self._validate_field_path(
            field_path=_condition_field_path(condition),
            ui_section=ui_section,
            owner=_condition_owner(step),
        )

    def _validate_field_path(
        self,
        field_path: str | None,
        ui_section: str,
        owner: str,
    ) -> None:
        if self.field_catalog is None or field_path is None:
            return

        if not self.field_catalog.has_field(field_path):
            raise ActionGroupValidatorError(
                f"{owner} has unknown {ui_section} field '{field_path}'"
            )


def validate_action_group(
    action_group: ActionGroup,
    catalog: ActionCatalog,
    source_types: Iterable[str],
    condition_operators: Iterable[str],
    mapping_types: Iterable[str],
) -> None:
    ActionGroupValidator(
        catalog=catalog,
        source_types=tuple(source_types),
        condition_operators=tuple(condition_operators),
        mapping_types=tuple(mapping_types),
    ).validate(action_group)


def validate_action_group_with_context(
    action_group: ActionGroup,
    context: ActionUiContext,
) -> None:
    ActionGroupValidator.from_context(context).validate(action_group)


def _condition_values(condition_group: ConditionGroup) -> list[str]:
    values: list[str] = []
    for condition in condition_group.conditions:
        if isinstance(condition.value, str):
            values.append(condition.value)
    return values


def _condition_owner(step: ActionStep | None) -> str:
    if step is None:
        return "Action Group"
    return f"Action #{step.order} '{step.name}'"


def _condition_field_path(condition: ConditionItem) -> str:
    if condition.field.startswith(f"{condition.record}."):
        return condition.field
    return f"{condition.record}.{condition.field}"


def _mapped_target_path(target: str, record_type: str) -> str:
    if target.startswith(f"{record_type}."):
        return target
    return f"{record_type}.{target}"


def _mapping_field_paths(mapping: MappingValue) -> list[str]:
    paths: list[str] = []

    if mapping.type == "variable":
        field_path = _mapping_variable_path(mapping)
        if field_path is not None:
            paths.append(field_path)

    if mapping.type == "multi_variable":
        for variable in mapping.variables:
            field_path = _variable_field_path(variable)
            if field_path is not None:
                paths.append(field_path)

    return paths


def _mapping_variable_path(mapping: MappingValue) -> str | None:
    if "mappedVariable" in mapping.extra:
        return mapping.extra["mappedVariable"]
    if isinstance(mapping.value, str):
        return mapping.value
    if mapping.variables:
        return _variable_field_path(mapping.variables[0])
    return None


def _variable_field_path(variable: dict) -> str | None:
    value = (
        variable.get("value")
        or variable.get("path")
        or variable.get("field")
        or variable.get("mappedVariable")
    )
    if isinstance(value, str):
        return value
    return None
