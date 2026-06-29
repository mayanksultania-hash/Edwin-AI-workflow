"""Known Action UI field paths used for validation."""

from dataclasses import dataclass, field
from typing import Any


class ActionFieldCatalogValidationError(ValueError):
    """Raised when field catalog data is not valid."""


@dataclass(frozen=True)
class ActionFieldCatalog:
    fields: tuple[str, ...]
    wildcard_prefixes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionFieldCatalog":
        if not isinstance(data, dict):
            raise ActionFieldCatalogValidationError("field catalog data must be an object")

        catalog_data = data.get("action_field_catalog", data)
        if not isinstance(catalog_data, dict):
            raise ActionFieldCatalogValidationError("action_field_catalog must be an object")

        fields = _load_string_list(catalog_data.get("fields"), "field catalog fields")
        wildcard_prefixes = _load_string_list(
            catalog_data.get("wildcard_prefixes", []),
            "field catalog wildcard_prefixes",
        )

        _ensure_unique_strings(fields, "field")
        _ensure_unique_strings(wildcard_prefixes, "wildcard prefix")

        return cls(fields=tuple(fields), wildcard_prefixes=tuple(wildcard_prefixes))

    def has_field(self, field_path: str) -> bool:
        path = field_path.strip()
        if path in self.fields:
            return True
        return any(path.startswith(prefix) for prefix in self.wildcard_prefixes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_field_catalog": {
                "fields": list(self.fields),
                "wildcard_prefixes": list(self.wildcard_prefixes),
            }
        }


def _load_string_list(raw_values: Any, label: str) -> list[str]:
    if not isinstance(raw_values, list):
        raise ActionFieldCatalogValidationError(f"{label} must be a list")

    values: list[str] = []
    for value in raw_values:
        if not isinstance(value, str) or not value.strip():
            raise ActionFieldCatalogValidationError(f"{label} must contain non-empty strings")
        values.append(value.strip())

    return values


def _ensure_unique_strings(values: list[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ActionFieldCatalogValidationError(f"duplicate {label}: {value}")
        seen.add(value)
