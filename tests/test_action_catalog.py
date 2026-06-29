from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.mcp.action_catalog_context import (
    ActionCatalogSourceError,
    HttpActionCatalogSource,
    StaticActionCatalogSource,
    build_default_action_catalog,
    build_default_action_catalog_source,
)
from ai_workflow.models.action_catalog import (
    ActionCatalog,
    ActionCatalogValidationError,
)


def valid_action_catalog_data():
    return {
        "action_catalog": {
            "actions": [
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
            ]
        }
    }


def test_action_catalog_from_dict_builds_model():
    catalog = ActionCatalog.from_dict(valid_action_catalog_data())

    assert catalog.action_names() == ("Update Insight", "Delay Action Execution")
    assert catalog.has_action("Update Insight") is True
    assert catalog.has_action("Create Alert") is False

    update_insight = catalog.get_action("Update Insight")
    assert update_insight.action_id == "mock-update-insight"
    assert update_insight.record_type == "insights"
    assert update_insight.outcomes == ("Insight updated", "Insight not found")
    assert update_insight.config_field_names() == ("add_additional_alerts",)


def test_action_catalog_to_dict_round_trips_shape():
    catalog = ActionCatalog.from_dict(valid_action_catalog_data())

    assert catalog.to_dict() == valid_action_catalog_data()


def test_action_catalog_preserves_action_service_metadata():
    data = valid_action_catalog_data()
    data["action_catalog"]["actions"][0]["schema_version"] = "20201028.01"
    data["action_catalog"]["actions"][0]["supportsMultipleRecords"] = True
    data["action_catalog"]["actions"][0]["action_config"][0].update(
        {
            "description": "Add related alerts",
            "title": "Add Additional Alerts",
            "fieldType": "boolean",
            "value": False,
        }
    )

    catalog = ActionCatalog.from_dict(data)
    update_insight = catalog.get_action("Update Insight")

    assert update_insight.schema_version == "20201028.01"
    assert update_insight.extra == {"supportsMultipleRecords": True}
    assert update_insight.action_config[0].extra == {
        "description": "Add related alerts",
        "title": "Add Additional Alerts",
        "fieldType": "boolean",
        "value": False,
    }
    assert catalog.to_dict() == data


def test_action_catalog_accepts_unwrapped_data():
    catalog = ActionCatalog.from_dict(valid_action_catalog_data()["action_catalog"])

    assert catalog.action_names() == ("Update Insight", "Delay Action Execution")


def test_action_catalog_rejects_duplicate_action_names():
    data = valid_action_catalog_data()
    data["action_catalog"]["actions"][1]["action_name"] = "Update Insight"

    with pytest.raises(ActionCatalogValidationError, match="duplicate action name"):
        ActionCatalog.from_dict(data)


def test_action_catalog_rejects_duplicate_outcomes():
    data = valid_action_catalog_data()
    data["action_catalog"]["actions"][0]["outcomes"] = [
        "Insight updated",
        "Insight updated",
    ]

    with pytest.raises(ActionCatalogValidationError, match="duplicate action spec"):
        ActionCatalog.from_dict(data)


def test_action_catalog_rejects_duplicate_config_fields():
    data = valid_action_catalog_data()
    data["action_catalog"]["actions"][0]["action_config"].append(
        {
            "name": "add_additional_alerts",
            "type": "boolean",
        }
    )

    with pytest.raises(ActionCatalogValidationError, match="duplicate config field"):
        ActionCatalog.from_dict(data)


def test_action_catalog_get_action_rejects_unknown_action():
    catalog = ActionCatalog.from_dict(valid_action_catalog_data())

    with pytest.raises(ActionCatalogValidationError, match="unknown action type"):
        catalog.get_action("Create Freshservice Ticket")


def test_static_action_catalog_source_loads_catalog():
    source = StaticActionCatalogSource(catalog_data=valid_action_catalog_data())

    catalog = source.load_catalog()

    assert catalog.has_action("Update Insight")
    assert catalog.get_action("Delay Action Execution").config_field_names() == (
        "delay_minutes",
    )


def test_default_action_catalog_source_matches_default_catalog():
    source_catalog = build_default_action_catalog_source().load_catalog()
    default_catalog = build_default_action_catalog()

    assert source_catalog.to_dict() == default_catalog.to_dict()


def test_default_action_catalog_matches_action_ui_examples():
    catalog = build_default_action_catalog()

    assert catalog.has_action("Lookup internal rowkey")
    assert catalog.has_action("Update Insight")
    assert catalog.has_action("Delay Action Execution")
    assert catalog.has_action("Update SNC Incident")
    assert catalog.has_action("Update Alert")
    assert catalog.has_action("Alert AI Investigation")
    assert catalog.has_action("Check Ansible Job")
    assert catalog.has_action("Execute Ansible Playbook")

    delay = catalog.get_action("Delay Action Execution")
    assert delay.record_type == "jsonResponse"
    assert delay.outcomes == ("Delay Completed",)
    assert delay.config_field_names() == ("delay_minutes",)

    update_alert = catalog.get_action("Update Alert")
    assert update_alert.record_type == "alerts"
    assert "Alert updated" in update_alert.outcomes


def test_http_action_catalog_source_loads_action_spec_response():
    calls = []

    def fake_get_json(url, headers, timeout_seconds):
        calls.append((url, headers, timeout_seconds))
        return {
            "actions": [
                {
                    "actionName": "Create Alert",
                    "actionId": "real-create-alert",
                    "recordType": "alerts",
                    "outcomes": ["Alert created"],
                    "actionConfig": [
                        {
                            "name": "severity",
                            "type": "string",
                            "label": "Severity",
                            "title": "Severity",
                            "fieldType": "text",
                            "defaultValue": "critical",
                            "required": True,
                        }
                    ],
                    "schemaVersion": "20201028.01",
                    "supportsMultipleRecords": True,
                }
            ]
        }

    source = HttpActionCatalogSource(
        base_url="http://action:8447/",
        headers={"Authorization": "Bearer test"},
        timeout_seconds=3.0,
        http_get_json=fake_get_json,
    )

    catalog = source.load_catalog()

    assert calls == [
        ("http://action:8447/action/spec", {"Authorization": "Bearer test"}, 3.0)
    ]
    create_alert = catalog.get_action("Create Alert")
    assert create_alert.action_id == "real-create-alert"
    assert create_alert.record_type == "alerts"
    assert create_alert.outcomes == ("Alert created",)
    assert create_alert.schema_version == "20201028.01"
    assert create_alert.extra == {"supportsMultipleRecords": True}
    assert create_alert.action_config[0].name == "severity"
    assert create_alert.action_config[0].extra["title"] == "Severity"
    assert create_alert.action_config[0].extra["fieldType"] == "text"
    assert create_alert.action_config[0].default == "critical"
    assert create_alert.action_config[0].required is True


def test_http_action_catalog_source_accepts_top_level_list_response():
    source = HttpActionCatalogSource(
        base_url="http://action:8447",
        http_get_json=lambda url, headers, timeout_seconds: [
            {
                "actionName": "Update Alert",
                "actionId": "real-update-alert",
                "recordType": "alerts",
                "outcomes": ["Alert updated"],
            }
        ],
    )

    catalog = source.load_catalog()

    assert catalog.get_action("Update Alert").action_id == "real-update-alert"


def test_http_action_catalog_source_accepts_already_normalized_response():
    source = HttpActionCatalogSource(
        base_url="http://action:8447",
        http_get_json=lambda url, headers, timeout_seconds: valid_action_catalog_data(),
    )

    catalog = source.load_catalog()

    assert catalog.action_names() == ("Update Insight", "Delay Action Execution")


def test_http_action_catalog_source_rejects_response_without_actions():
    source = HttpActionCatalogSource(
        base_url="http://action:8447",
        http_get_json=lambda url, headers, timeout_seconds: {"unexpected": []},
    )

    with pytest.raises(ActionCatalogSourceError, match="actions list"):
        source.load_catalog()
