"""Action UI field catalog sources."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Protocol

from ai_workflow.models.action_field_catalog import ActionFieldCatalog


class ActionFieldCatalogSource(Protocol):
    """Loads Action UI field paths."""

    def load_catalog(self) -> ActionFieldCatalog:
        """Return field paths used for Action Group generation and validation."""


class ActionFieldCatalogSourceError(RuntimeError):
    """Raised when field catalog data cannot be loaded."""


@dataclass(frozen=True)
class StaticActionFieldCatalogSource:
    """Loads field paths from local data."""

    catalog_data: dict

    def load_catalog(self) -> ActionFieldCatalog:
        return ActionFieldCatalog.from_dict(self.catalog_data)


@dataclass(frozen=True)
class FileActionFieldCatalogSource:
    """Loads field paths from global_fields-style JSON files."""

    paths: tuple[Path, ...]
    extra_fields: tuple[str, ...] = field(default_factory=tuple)
    wildcard_prefixes: tuple[str, ...] = field(default_factory=tuple)

    def load_catalog(self) -> ActionFieldCatalog:
        fields: set[str] = set(self.extra_fields)
        wildcard_prefixes: set[str] = set(self.wildcard_prefixes)

        for path in self.paths:
            catalog = _normalize_field_catalog_data(_load_json_file(path))
            fields.update(catalog.fields)
            wildcard_prefixes.update(catalog.wildcard_prefixes)

        return ActionFieldCatalog(
            fields=tuple(sorted(fields)),
            wildcard_prefixes=tuple(sorted(wildcard_prefixes)),
        )


def build_default_action_field_catalog_source() -> ActionFieldCatalogSource:
    return StaticActionFieldCatalogSource(catalog_data=_default_action_field_catalog_data())


def build_default_action_field_catalog() -> ActionFieldCatalog:
    return build_default_action_field_catalog_source().load_catalog()


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ActionFieldCatalogSourceError(f"Field catalog file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ActionFieldCatalogSourceError(f"Field catalog file must be valid JSON: {path}") from error


def _normalize_field_catalog_data(data: Any) -> ActionFieldCatalog:
    if isinstance(data, dict) and "action_field_catalog" in data:
        return ActionFieldCatalog.from_dict(data)

    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return _normalize_global_fields(data["records"])

    if isinstance(data, list):
        return _normalize_field_list(data)

    raise ActionFieldCatalogSourceError("Field catalog data must contain records or fields")


def _normalize_global_fields(records: list[Any]) -> ActionFieldCatalog:
    fields: set[str] = set()
    wildcard_prefixes: set[str] = set(DEFAULT_FIELD_WILDCARD_PREFIXES)

    for record in records:
        if not isinstance(record, dict):
            raise ActionFieldCatalogSourceError("global_fields records must be objects")

        record_type = record.get("recordType")
        if not isinstance(record_type, str) or not record_type.strip():
            raise ActionFieldCatalogSourceError("global_fields record must include recordType")

        for field_data in record.get("fields", []) or []:
            if not isinstance(field_data, dict):
                raise ActionFieldCatalogSourceError("global_fields fields must be objects")

            field_name = field_data.get("name")
            if not isinstance(field_name, str) or not field_name.strip():
                raise ActionFieldCatalogSourceError("global_fields field must include name")

            fields.add(f"{record_type}.{field_name.strip()}")
            if record_type == "alerts":
                fields.add(f"alert.{field_name.strip()}")

    fields.update(DEFAULT_FIELD_PATHS)
    return ActionFieldCatalog(
        fields=tuple(sorted(fields)),
        wildcard_prefixes=tuple(sorted(wildcard_prefixes)),
    )


def _normalize_field_list(raw_fields: list[Any]) -> ActionFieldCatalog:
    fields: set[str] = set(DEFAULT_FIELD_PATHS)
    wildcard_prefixes: set[str] = set(DEFAULT_FIELD_WILDCARD_PREFIXES)

    for raw_field in raw_fields:
        if isinstance(raw_field, str):
            fields.add(raw_field.strip())
            continue
        if isinstance(raw_field, dict):
            value = raw_field.get("path") or raw_field.get("field") or raw_field.get("name")
            if isinstance(value, str) and value.strip():
                fields.add(value.strip())
                continue
        raise ActionFieldCatalogSourceError("Field list entries must be strings or objects")

    return ActionFieldCatalog(
        fields=tuple(sorted(fields)),
        wildcard_prefixes=tuple(sorted(wildcard_prefixes)),
    )


DEFAULT_FIELD_PATHS = (
    "action_outcome.outcome",
    "actionsystem.Last Action Outcome",
    "actionsystem.User ID",
    "alert.alertDetails.alertState",
    "alert.alertDetails.sncIncidentId",
    "alert.alertDetails.sncIncidentPriority",
    "alert.alertDetails.sncIncidentUrl",
    "alert.cf.eventDescription",
    "alert.cf.eventName",
    "alerts.Assigned To",
    "alerts.Severity",
    "alerts.State",
    "events.Severity",
    "insights.Escalation",
    "insights.Incident ID",
    "insights.Severity",
    "insights.State",
    "sncIncident.Incident Priority",
    "sncIncident.Incident URL",
    "sncIncident.State",
    "sncIncident.description",
    "sncIncident.number",
    "sncIncident.priority",
    "sncIncident.short_description",
    "sncIncident.url",
)

DEFAULT_FIELD_WILDCARD_PREFIXES = (
    "alerts.extra.",
    "events.extra.",
    "insights.extra.",
    "sncIncident.extra.",
)


def _default_action_field_catalog_data() -> dict:
    return {
        "action_field_catalog": {
            "fields": list(DEFAULT_FIELD_PATHS),
            "wildcard_prefixes": list(DEFAULT_FIELD_WILDCARD_PREFIXES),
        }
    }
