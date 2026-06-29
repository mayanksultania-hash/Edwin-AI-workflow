"""Action Service catalog context for Phase 2 development."""

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_workflow.models.action_catalog import ActionCatalog


class ActionCatalogSource(Protocol):
    """Loads Action Service action specs."""

    def load_catalog(self) -> ActionCatalog:
        """Return the catalog used for Action Group generation and validation."""


class ActionCatalogSourceError(RuntimeError):
    """Raised when an Action Service catalog source cannot load a catalog."""


@dataclass(frozen=True)
class StaticActionCatalogSource:
    """Loads a catalog from local data."""

    catalog_data: dict

    def load_catalog(self) -> ActionCatalog:
        return ActionCatalog.from_dict(self.catalog_data)


@dataclass(frozen=True)
class HttpActionCatalogSource:
    """Loads an org-specific catalog from Action Service GET /action/spec."""

    base_url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 10.0
    http_get_json: Callable[[str, dict[str, str], float], Any] | None = None

    def load_catalog(self) -> ActionCatalog:
        data = self._get_json(self._spec_url())
        return ActionCatalog.from_dict(_normalize_action_spec_response(data))

    def _spec_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/action/spec"

    def _get_json(self, url: str) -> Any:
        if self.http_get_json:
            return self.http_get_json(url, self.headers, self.timeout_seconds)

        return _default_http_get_json(url, self.headers, self.timeout_seconds)


def build_default_action_catalog_source() -> ActionCatalogSource:
    return StaticActionCatalogSource(catalog_data=_default_action_catalog_data())


def build_default_action_catalog() -> ActionCatalog:
    return build_default_action_catalog_source().load_catalog()


def _default_http_get_json(
    url: str,
    headers: dict[str, str],
    timeout_seconds: float,
) -> Any:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise ActionCatalogSourceError(
            f"Action catalog request failed with HTTP {error.code}: {url}"
        ) from error
    except URLError as error:
        raise ActionCatalogSourceError(
            f"Action catalog request failed: {url}"
        ) from error

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as error:
        raise ActionCatalogSourceError(
            "Action catalog response must be valid JSON"
        ) from error


def _normalize_action_spec_response(data: Any) -> dict[str, Any]:
    if isinstance(data, list):
        raw_actions = data
    elif isinstance(data, dict):
        raw_actions = (
            data.get("actions")
            or data.get("actionSpecs")
            or data.get("specs")
            or data.get("data")
        )
        if raw_actions is None and "action_catalog" in data:
            return data
    else:
        raise ActionCatalogSourceError("Action catalog response must be an object or list")

    if not isinstance(raw_actions, list):
        raise ActionCatalogSourceError("Action catalog response must contain an actions list")

    return {
        "action_catalog": {
            "actions": [_normalize_action_spec(action) for action in raw_actions],
        }
    }


def _normalize_action_spec(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ActionCatalogSourceError("Action catalog action spec must be an object")

    normalized = {
        "action_name": _first_present(data, "action_name", "actionName", "name"),
        "action_id": _first_present(data, "action_id", "actionId", "id"),
        "record_type": _first_present(data, "record_type", "recordType"),
        "outcomes": data.get("outcomes") or data.get("actionOutcomes") or [],
        "action_config": [
            _normalize_action_config_field(field)
            for field in data.get("action_config", data.get("actionConfig", [])) or []
        ],
    }

    schema_version = data.get("schema_version") or data.get("schemaVersion")
    if schema_version is not None:
        normalized["schema_version"] = schema_version
    if "supportsMultipleRecords" in data:
        normalized["supportsMultipleRecords"] = data["supportsMultipleRecords"]

    return normalized


def _normalize_action_config_field(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ActionCatalogSourceError("Action catalog config field must be an object")

    normalized = {
        "name": _first_present(data, "name", "key", "fieldName"),
        "type": _first_present(data, "type", "fieldType"),
    }

    label = data.get("label") or data.get("displayName")
    if label is not None:
        normalized["label"] = label
    for key in ("description", "title", "fieldType", "value"):
        if key in data:
            normalized[key] = data[key]
    if "default" in data:
        normalized["default"] = data["default"]
    elif "defaultValue" in data:
        normalized["default"] = data["defaultValue"]
    if "required" in data:
        normalized["required"] = data["required"]

    return normalized


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value

    raise ActionCatalogSourceError(f"Action catalog field missing one of: {', '.join(keys)}")


def _default_action_catalog_data() -> dict:
    return {
        "action_catalog": {
            "actions": [
                {
                    "action_name": "Lookup internal rowkey",
                    "action_id": "mock-lookup-internal-rowkey",
                    "record_type": "jsonResponse",
                    "outcomes": ["Rowkey found", "Rowkey not found"],
                },
                {
                    "action_name": "Update Insight",
                    "action_id": "mock-update-insight",
                    "record_type": "insights",
                    "outcomes": ["Insight updated", "Insight not found"],
                    "action_config": [
                        {
                            "name": "add_additional_alerts",
                            "type": "boolean",
                            "label": "Add Additional Alerts",
                            "default": False,
                        }
                    ],
                },
                {
                    "action_name": "Delay Action Execution",
                    "action_id": "mock-delay-action-execution",
                    "record_type": "jsonResponse",
                    "outcomes": ["Delay Completed"],
                    "action_config": [
                        {
                            "name": "delay_minutes",
                            "type": "number",
                            "label": "Delay Minutes",
                            "default": 5,
                            "required": True,
                        }
                    ],
                },
                {
                    "action_name": "Update SNC Incident",
                    "action_id": "mock-update-snc-incident",
                    "record_type": "sncIncident",
                    "outcomes": ["SNC Incident updated", "SNC Incident not found"],
                },
                {
                    "action_name": "Update Alert",
                    "action_id": "mock-update-alert",
                    "record_type": "alerts",
                    "outcomes": ["Alert updated", "Alert does not exist"],
                    "action_config": [
                        {
                            "name": "add_additional_alerts",
                            "type": "boolean",
                            "label": "Add Additional Alerts",
                            "default": False,
                        }
                    ],
                },
                {
                    "action_name": "Alert AI Investigation",
                    "action_id": "mock-alert-ai-investigation",
                    "record_type": "alerts",
                    "outcomes": ["Investigation created", "Investigation skipped"],
                    "action_config": [
                        {
                            "name": "location_field_mappings",
                            "type": "object",
                            "label": "Location field mappings",
                            "default": {},
                        }
                    ],
                },
                {
                    "action_name": "Check Ansible Job",
                    "action_id": "mock-check-ansible-job",
                    "record_type": "ansiblePlaybook",
                    "outcomes": ["Job completed", "Job running", "Job failed"],
                },
                {
                    "action_name": "Execute Ansible Playbook",
                    "action_id": "mock-execute-ansible-playbook",
                    "record_type": "ansiblePlaybook",
                    "outcomes": ["Playbook started", "Playbook failed"],
                    "action_config": [
                        {
                            "name": "playbook_name",
                            "type": "string",
                            "label": "Playbook Name",
                            "required": True,
                        }
                    ],
                },
            ]
        }
    }
