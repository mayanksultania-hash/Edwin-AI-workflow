"""Load reusable Action ID metadata for LM Alert Processing prompts.

YAML layout:
- ``field_sets.yaml`` — shared field lists (caller_id, severity paths, etc.)
- ``action_ids.yaml`` — one entry per Action ID type, referencing field sets by name
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ai_workflow.action_groups.common.action_schemas.base import (
    ActionFieldDescription,
    ActionSchemaDescription,
    render_action_schema_prompt_context,
)

_CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_FIELD_SETS_PATH = _CONFIG_DIR / "field_sets.yaml"
DEFAULT_ACTION_IDS_PATH = _CONFIG_DIR / "action_ids.yaml"


class LMAlertActionIdConfig:
    """Load Action ID schema metadata from ``field_sets.yaml`` and ``action_ids.yaml``."""

    def __init__(
        self,
        field_sets_path: Path = DEFAULT_FIELD_SETS_PATH,
        action_ids_path: Path = DEFAULT_ACTION_IDS_PATH,
    ) -> None:
        self.field_sets_path = field_sets_path
        self.action_ids_path = action_ids_path

    def load(self) -> list[ActionSchemaDescription]:
        field_sets = self._load_field_sets()
        action_ids = self._load_action_ids()
        return [_build_action_schema(entry, field_sets) for entry in action_ids]

    def _load_field_sets(self) -> dict[str, list[dict[str, Any]]]:
        if not self.field_sets_path.is_file():
            raise FileNotFoundError(f"Action ID field sets not found: {self.field_sets_path}")

        raw = yaml.safe_load(self.field_sets_path.read_text(encoding="utf-8")) or {}
        field_sets = raw.get("field_sets")
        if not isinstance(field_sets, dict) or not field_sets:
            raise ValueError(
                f"Action ID field sets must contain a non-empty 'field_sets' mapping: "
                f"{self.field_sets_path}"
            )
        return field_sets

    def _load_action_ids(self) -> list[dict[str, Any]]:
        if not self.action_ids_path.is_file():
            raise FileNotFoundError(f"Action ID catalog not found: {self.action_ids_path}")

        raw = yaml.safe_load(self.action_ids_path.read_text(encoding="utf-8")) or {}
        action_ids = raw.get("action_ids")
        if not isinstance(action_ids, list) or not action_ids:
            raise ValueError(
                f"Action ID catalog must contain a non-empty 'action_ids' list: "
                f"{self.action_ids_path}"
            )
        return action_ids


def _build_action_schema(
    schema: dict[str, Any],
    field_sets: dict[str, list[dict[str, Any]]],
) -> ActionSchemaDescription:
    return ActionSchemaDescription(
        action_name=schema["action_name"],
        action_id=schema.get("action_id"),
        use_for=schema["use_for"],
        patch_guidance=schema["patch_guidance"],
        mapping_fields=_resolve_fields(
            field_sets=field_sets,
            field_set_names=schema.get("mapping_field_sets"),
            inline_fields=schema.get("mapping_fields"),
        ),
        precondition_fields=_resolve_fields(
            field_sets=field_sets,
            field_set_names=schema.get("precondition_field_sets"),
            inline_fields=schema.get("precondition_fields"),
        ),
        action_config_fields=_resolve_fields(
            field_sets=field_sets,
            field_set_names=schema.get("action_config_field_sets"),
            inline_fields=schema.get("action_config_fields"),
        ),
        examples=schema.get("examples", []),
    )


def _resolve_fields(
    field_sets: dict[str, list[dict[str, Any]]],
    field_set_names: list[str] | None,
    inline_fields: list[dict[str, Any]] | None,
) -> list[ActionFieldDescription]:
    fields: list[ActionFieldDescription] = []

    for set_name in field_set_names or []:
        if set_name not in field_sets:
            raise ValueError(f"Unknown field set: {set_name!r}")
        for field in field_sets[set_name]:
            fields.append(ActionFieldDescription.model_validate(field))

    for field in inline_fields or []:
        fields.append(ActionFieldDescription.model_validate(field))

    return fields


@lru_cache(maxsize=1)
def _cached_lm_alert_action_ids() -> tuple[ActionSchemaDescription, ...]:
    return tuple(LMAlertActionIdConfig().load())


def build_lm_alert_action_id_schemas() -> list[ActionSchemaDescription]:
    """Return reusable Action ID schemas used in LM Alert Processing."""

    return list(_cached_lm_alert_action_ids())


def build_lm_alert_action_id_prompt_context() -> str:
    """Return compact Action ID guidance for LM Alert prompts."""

    return render_action_schema_prompt_context(build_lm_alert_action_id_schemas())


# Backward-compatible aliases.
build_lm_alert_action_schemas = build_lm_alert_action_id_schemas
build_lm_alert_action_schema_prompt_context = build_lm_alert_action_id_prompt_context
