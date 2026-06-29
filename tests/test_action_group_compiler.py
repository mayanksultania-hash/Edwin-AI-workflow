from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPANY_PROJECTS_ROOT = PROJECT_ROOT.parent
FIXTURE_PATH = (
    COMPANY_PROJECTS_ROOT
    / "OpsDirector-RulesService"
    / "src"
    / "test"
    / "resources"
    / "fixtures"
    / "responses"
    / "actionGroupCreateIncident.json"
)
ADDITIONAL_RECORDS_FIXTURE_PATH = (
    COMPANY_PROJECTS_ROOT
    / "OpsDirector-ActionService"
    / "src"
    / "test"
    / "resources"
    / "fixtures"
    / "group"
    / "create_alert_additionalrecords.json"
)
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.action_group_compiler import (
    compile_action_group_to_action_service_json,
)
from ai_workflow.models.action_catalog import ActionCatalog
from ai_workflow.models.action_group import ActionGroup


def create_incident_catalog() -> ActionCatalog:
    return ActionCatalog.from_dict(
        {
            "action_catalog": {
                "actions": [
                    {
                        "action_name": "Create SNC Incident",
                        "action_id": "a088ee7d-22cd-4cd2-bc9d-2a9d147a7552",
                        "record_type": "sncIncident",
                        "outcomes": [
                            "SNC Incident already exists",
                            "SNC Incident created",
                        ],
                        "action_config": [
                            {
                                "name": "retries",
                                "type": "number",
                                "default": 5,
                            },
                            {
                                "name": "timeouts",
                                "type": "number",
                                "default": 20,
                            },
                        ],
                    },
                    {
                        "action_name": "Update Alert",
                        "action_id": "a19a3f7d-4f5f-43aa-ab2e-e32d713ad598",
                        "record_type": "alerts",
                        "outcomes": [
                            "Alert updated",
                            "Alert does not exist",
                        ],
                        "action_config": [
                            {
                                "name": "retries",
                                "type": "number",
                                "default": 5,
                            },
                            {
                                "name": "timeouts",
                                "type": "number",
                                "default": 20,
                            },
                        ],
                    },
                ]
            }
        }
    )


def create_incident_action_group() -> ActionGroup:
    return ActionGroup.from_dict(
        {
            "action_group": {
                "name": "Create an Incident",
                "description": "Create an SNC Incident From an Alert",
                "source": "alerts",
                "rule": None,
                "group_condition": {
                    "operator": "EQUALS",
                    "conditions": [
                        {
                            "record": "alert",
                            "field": "alertDetails.alertState",
                            "operator": "EQUALS",
                            "value": "assigned",
                        }
                    ],
                },
                "steps": [
                    {
                        "order": 1,
                        "id": "create_snc_incident",
                        "action_type": "Create SNC Incident",
                        "name": "Create SNC Incident",
                        "description": "Create SNC Incident",
                        "mapped_fields": [
                            {
                                "target": "sncIncident.short_description",
                                "mappings": [
                                    {
                                        "type": "multi_variable",
                                        "format": "Created for OPSD Event %s: %s",
                                        "variables": [
                                            {"path": "alert.cf.eventName"},
                                            {"path": "alert.cf.eventDescription"},
                                        ],
                                    }
                                ],
                            },
                            {
                                "target": "sncIncident.description",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "alert.cf.eventName",
                                    }
                                ],
                            },
                        ],
                        "stop_condition": {
                            "operator": "OR",
                            "conditions": [
                                {
                                    "record": "action_outcome",
                                    "field": "outcome",
                                    "operator": "EQUALS",
                                    "value": "SNC Incident already exists",
                                }
                            ],
                        },
                    },
                    {
                        "order": 2,
                        "id": "update_alert",
                        "action_type": "Update Alert",
                        "name": "Update Alert",
                        "description": "Update Alert",
                        "mapped_fields": [
                            {
                                "target": "alert.alertDetails.sncIncidentId",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "sncIncident.number",
                                    }
                                ],
                            },
                            {
                                "target": "alert.alertDetails.sncIncidentUrl",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "sncIncident.url",
                                    }
                                ],
                            },
                            {
                                "target": "alert.alertDetails.sncIncidentPriority",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "sncIncident.priority",
                                    }
                                ],
                            },
                            {
                                "target": "alert.alertDetails.alertState",
                                "mappings": [
                                    {
                                        "type": "value",
                                        "value": "incident/open",
                                    }
                                ],
                            },
                        ],
                        "stop_condition": {
                            "operator": "OR",
                            "conditions": [
                                {
                                    "record": "action_outcome",
                                    "field": "outcome",
                                    "operator": "EQUALS",
                                    "value": "Alert does not exist",
                                }
                            ],
                        },
                    },
                ],
            }
        }
    )


def create_alert_additional_records_catalog() -> ActionCatalog:
    return ActionCatalog.from_dict(
        {
            "action_catalog": {
                "actions": [
                    {
                        "action_name": "Update Alert",
                        "action_id": "a19a3f7d-4f5f-43aa-ab2e-e32d713ad598",
                        "record_type": "alerts",
                        "schema_version": "20201028.01",
                        "supportsMultipleRecords": True,
                        "outcomes": [
                            "Alert updated",
                            "Alert does not exist",
                            "Alert updated - late event",
                            "Alert key not available",
                            "Action Skipped",
                            "Action Failed",
                        ],
                        "action_config": [
                            {
                                "description": (
                                    "Field containing an alternate value to use as the Alert key"
                                ),
                                "name": "keyField",
                                "title": "Alert key",
                                "fieldType": "recordTypeAndField",
                                "type": "string",
                            },
                            {
                                "description": (
                                    "Add related Insights to additional records list, if true"
                                ),
                                "name": "additionalInsights",
                                "title": "Enable Additional Insights",
                                "value": False,
                                "fieldType": "boolean",
                                "type": "boolean",
                            },
                            {
                                "description": "Apply a strict time ordering to processing events",
                                "name": "strictOrder",
                                "title": "Enable Strict ordering",
                                "value": False,
                                "fieldType": "boolean",
                                "type": "boolean",
                            },
                        ],
                    },
                    {
                        "action_name": "Create Alert",
                        "action_id": "f9d471e1-e453-4b25-adee-3ace0939cd31",
                        "record_type": "alerts",
                        "outcomes": [
                            "Alert created",
                            "Alert exists",
                            "Alert key not available",
                            "Action Skipped",
                            "Action Failed",
                        ],
                        "action_config": [
                            {
                                "name": "keyField",
                                "type": "string",
                            },
                            {
                                "name": "additionalInsights",
                                "type": "boolean",
                                "value": False,
                            },
                            {
                                "name": "stateField",
                                "type": "string",
                                "value": "alertDetails.alertState",
                            },
                            {
                                "name": "closedState",
                                "type": "string",
                                "value": "closed",
                            },
                            {
                                "name": "newState",
                                "type": "string",
                                "value": "new",
                            },
                            {
                                "name": "sdtState",
                                "type": "string",
                                "value": "sdt",
                            },
                        ],
                    },
                ]
            }
        }
    )


def create_alert_additional_records_action_group() -> ActionGroup:
    return ActionGroup.from_dict(
        {
            "action_group": {
                "name": "Create Alert",
                "description": "Create an Alert from an Event - multiple records test",
                "source": "events",
                "rule": None,
                "steps": [
                    {
                        "order": 1,
                        "id": "update_alert",
                        "action_type": "Update Alert",
                        "name": "Update alert",
                        "description": "maintain alert count",
                        "config": {"keyField": "meta.alertKey"},
                        "use_additional_records": True,
                        "mapped_fields": [
                            {
                                "target": "meta.eventCount",
                                "mappings": [{"type": "increment_value"}],
                            },
                            {
                                "target": "alertDetails.alertState",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "alerts.alertDetails.alertState",
                                    },
                                    {
                                        "type": "value",
                                        "value": "cleared",
                                        "only_when": {
                                            "operator": "EQUALS",
                                            "conditions": [
                                                {
                                                    "record": "events",
                                                    "field": "cf.eventSeverity",
                                                    "operator": "EQUALS",
                                                    "value": 0,
                                                }
                                            ],
                                        },
                                    },
                                ],
                            },
                            {
                                "target": "alertDetails.currentSeverity",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "events.cf.eventSeverity",
                                        "only_when": {
                                            "operator": "GREATER_THAN",
                                            "conditions": [
                                                {
                                                    "record": "events",
                                                    "field": "cf.eventSeverity",
                                                    "operator": "GREATER_THAN",
                                                    "value": 3,
                                                }
                                            ],
                                        },
                                    }
                                ],
                            },
                            {
                                "target": "meta.updatedTimestamp",
                                "mappings": [
                                    {
                                        "type": "variable",
                                        "value": "actionsystem.action.startTime",
                                    }
                                ],
                            },
                        ],
                        "stop_condition": {
                            "operator": "OR",
                            "conditions": [
                                {
                                    "record": "action_outcome",
                                    "field": "outcome",
                                    "operator": "EQUALS",
                                    "value": "Alert updated",
                                }
                            ],
                        },
                    },
                    {
                        "order": 2,
                        "id": "create_new_alert",
                        "action_type": "Create Alert",
                        "name": "Create new alert",
                        "description": "when an alert does not already exist",
                        "config": {
                            "stateField": "alertDetails.alertState",
                            "closedState": "closed",
                            "newState": "new",
                        },
                    },
                ],
            }
        }
    )


def test_compile_action_group_matches_real_create_incident_fixture_shape():
    fixture = _load_create_incident_fixture()
    compiled = compile_action_group_to_action_service_json(
        action_group=create_incident_action_group(),
        catalog=create_incident_catalog(),
    )

    assert _without_legacy_runtime_fields(compiled) == _without_legacy_runtime_fields(fixture)


def test_compile_action_group_matches_real_additional_records_fixture_shape():
    fixture = _load_additional_records_fixture()
    compiled = compile_action_group_to_action_service_json(
        action_group=create_alert_additional_records_action_group(),
        catalog=create_alert_additional_records_catalog(),
    )

    assert _without_runtime_fields(compiled) == _without_runtime_fields(fixture)


def test_compile_action_group_adds_step_precondition_from_start_condition():
    data = create_incident_action_group().to_dict()
    data["action_group"]["steps"][0]["start_condition"] = {
        "operator": "AND",
        "conditions": [
            {
                "record": "alert",
                "field": "alertDetails.alertState",
                "operator": "EQUALS",
                "value": "assigned",
            }
        ],
    }
    action_group = ActionGroup.from_dict(data)

    compiled = compile_action_group_to_action_service_json(
        action_group=action_group,
        catalog=create_incident_catalog(),
    )

    assert "uiCondition" in compiled
    assert "uiCondition" not in compiled["actions"][0]
    assert compiled["actions"][0]["preconditionV2"] == {
        "schemaName": "filterCondition",
        "schemaVersion": "4",
        "expression": {
            "AND": [
                {
                    "EQUALS": [
                        {
                            "field": "alert.alertDetails.alertState",
                            "type": "string",
                        },
                        "assigned",
                    ]
                }
            ]
        },
    }


def test_compile_action_group_adds_action_ui_entry_fields():
    data = create_incident_action_group().to_dict()
    data["action_group"]["steps"][0]["config"] = {"retries": 10}
    data["action_group"]["steps"][0]["preload"] = "alerts"
    data["action_group"]["steps"][0]["use_additional_records"] = True
    data["action_group"]["steps"][0]["mapped_fields"].append(
        {
            "target": "sncIncident.priority",
            "mappings": [
                {
                    "type": "value",
                    "value": "high",
                    "only_when": {
                        "operator": "GREATER_THAN",
                        "conditions": [
                            {
                                "record": "alert",
                                "field": "alertDetails.currentSeverity",
                                "operator": "GREATER_THAN",
                                "value": 3,
                            }
                        ],
                    },
                }
            ],
        }
    )
    action_group = ActionGroup.from_dict(data)

    compiled = compile_action_group_to_action_service_json(
        action_group=action_group,
        catalog=create_incident_catalog(),
    )

    entry = compiled["actions"][0]
    assert entry["actionSpecification"]["actionConfig"] == [
        {
            "name": "retries",
            "type": "number",
            "value": 5,
        },
        {
            "name": "timeouts",
            "type": "number",
            "value": 20,
        },
    ]
    assert entry["actionConfig"] == [
        {
            "name": "retries",
            "type": "number",
            "value": 10,
        }
    ]
    assert entry["preload"] == "alerts"
    assert entry["useAdditionalRecords"] is True
    assert entry["mappings"]["sncIncident.priority"] == [
        {
            "type": "value",
            "mappedValue": "high",
            "conditionV2": {
                "schemaName": "filterCondition",
                "schemaVersion": "4",
                "expression": {
                    "GREATER_THAN": [
                        {
                            "field": "alert.alertDetails.currentSeverity",
                            "type": "integer",
                        },
                        3,
                    ]
                },
            },
        }
    ]


def test_compile_action_group_supports_increment_value_mapping():
    data = create_incident_action_group().to_dict()
    data["action_group"]["steps"][1]["mapped_fields"].append(
        {
            "target": "alert.alertDetails.alertCount",
            "mappings": [
                {
                    "type": "increment_value",
                    "value": "alert.alertDetails.alertCount",
                }
            ],
        }
    )
    action_group = ActionGroup.from_dict(data)

    compiled = compile_action_group_to_action_service_json(
        action_group=action_group,
        catalog=create_incident_catalog(),
    )

    assert compiled["actions"][1]["mappings"]["alert.alertDetails.alertCount"] == [
        {
            "type": "increment_value",
            "incrementVariable": "alert.alertDetails.alertCount",
        }
    ]


def _load_create_incident_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_additional_records_fixture() -> dict:
    return json.loads(ADDITIONAL_RECORDS_FIXTURE_PATH.read_text(encoding="utf-8"))


def _without_runtime_fields(data: dict) -> dict:
    copied = dict(data)
    copied.pop("actionGroupId", None)
    copied.pop("writtenOn", None)
    return copied


def _without_legacy_runtime_fields(data: dict) -> dict:
    copied = _without_runtime_fields(data)
    for action in copied["actions"]:
        action.pop("name", None)
        action.pop("description", None)
    return copied
