from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.action_group import (
    ActionGroup,
    ActionGroupValidationError,
)


def valid_action_group_data():
    """Incident Processing v3.0 — all 8 flat steps (matches Phase 2 doc / OOTB UI example)."""
    return {
        "action_group": {
            "name": "Incident Processing v3.0",
            "description": (
                "Default action group to process ServiceNow incident updates "
                "sent from the LM-DX application"
            ),
            "source": "sncIncident",
            "rule": None,
            "group_condition": {
                "operator": "EQUALS",
                "conditions": [
                    {
                        "record": "sncIncident",
                        "field": "State",
                        "operator": "EQUALS",
                        "value": "Resolved",
                    }
                ],
            },
            "steps": [
                {
                    "order": 1,
                    "id": "lookup_incident_reference",
                    "action_type": "Lookup internal rowkey",
                    "name": "Lookup Incident reference",
                    "description": "Lookup Incident reference",
                },
                {
                    "order": 2,
                    "id": "store_incident_details_in_insight",
                    "action_type": "Update Insight",
                    "name": "Store Incident details in Insight",
                    "description": "Store Incident details in Insight",
                },
                {
                    "order": 3,
                    "id": "wait_if_incident_resolved_and_insight_active",
                    "action_type": "Delay Action Execution",
                    "name": "Wait for 5 min if Incident is Resolved and Insight is Active",
                    "description": (
                        "Wait for 5 min if Incident is Resolved and Insight is Active"
                    ),
                    "config": {"delay_minutes": 5},
                },
                {
                    "order": 4,
                    "id": "reopen_incident_if_insight_active",
                    "action_type": "Update SNC Incident",
                    "name": "Re-open Incident If Insight State is Active",
                    "description": "Re-open Incident If Insight State is Active",
                    "start_condition": {
                        "operator": "AND",
                        "conditions": [
                            {
                                "record": "actionsystem",
                                "field": "Last Action Outcome",
                                "operator": "EQUALS",
                                "value": "Delay Completed",
                            },
                            {
                                "record": "sncIncident",
                                "field": "State",
                                "operator": "EQUALS",
                                "value": "Resolved",
                            },
                            {
                                "record": "insights",
                                "field": "State",
                                "operator": "EQUALS",
                                "value": "active",
                            },
                            {
                                "record": "insights",
                                "field": "Severity",
                                "operator": "GREATER_THAN",
                                "value": "Warning",
                            },
                            {
                                "record": "insights",
                                "field": "insights.extra.Edwin_Incident_Auto...",
                                "operator": "EQUALS",
                                "value": False,
                            },
                        ],
                    },
                    "mapped_fields": [
                        {
                            "target": "State",
                            "mappings": [
                                {
                                    "type": "value",
                                    "value": "In Progress",
                                }
                            ],
                        }
                    ],
                },
                {
                    "order": 5,
                    "id": "store_incident_details_in_alert",
                    "action_type": "Update Alert",
                    "name": "Store Incident details in Alert",
                    "description": "Store Incident details in Alert",
                },
                {
                    "order": 6,
                    "id": "wait_if_incident_resolved_and_alert_active",
                    "action_type": "Delay Action Execution",
                    "name": "Wait for 5 min if Incident is Resolved and Alert is Active",
                    "description": (
                        "Wait for 5 min if Incident is Resolved and Alert is Active"
                    ),
                    "config": {"delay_minutes": 5},
                },
                {
                    "order": 7,
                    "id": "reopen_incident_if_singleton_alert_active",
                    "action_type": "Update SNC Incident",
                    "name": "Re-open Incident If Singleton Alert State is Active",
                    "description": "Re-open Incident If Singleton Alert State is Active",
                },
                {
                    "order": 8,
                    "id": "store_incident_details_in_additional_alerts",
                    "action_type": "Update Alert",
                    "name": "Store Incident details in additional Alerts",
                    "description": "Store Incident details in additional Alerts",
                    "use_additional_records": True,
                },
            ],
        }
    }


def test_action_group_from_dict_builds_model():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    assert action_group.name == "Incident Processing v3.0"
    assert action_group.source == "sncIncident"
    assert action_group.rule is None
    assert action_group.group_condition is not None
    assert action_group.group_condition.conditions[0].record == "sncIncident"
    assert len(action_group.steps) == 8

    assert action_group.steps[0].action_type == "Lookup internal rowkey"
    assert action_group.steps[1].action_type == "Update Insight"
    assert action_group.steps[2].config == {"delay_minutes": 5}
    assert action_group.steps[3].start_condition.conditions[0].record == "actionsystem"
    assert action_group.steps[3].mapped_fields[0].target == "State"
    assert action_group.steps[7].use_additional_records is True


def test_action_group_to_dict_round_trips_shape():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    assert action_group.to_dict() == valid_action_group_data()


def test_action_group_accepts_unwrapped_data():
    action_group = ActionGroup.from_dict(valid_action_group_data()["action_group"])

    assert action_group.name == "Incident Processing v3.0"
    assert len(action_group.steps) == 8


def test_action_group_requires_steps():
    data = valid_action_group_data()
    data["action_group"]["steps"] = []

    with pytest.raises(ActionGroupValidationError, match="at least one step"):
        ActionGroup.from_dict(data)


def test_action_group_rejects_duplicate_step_ids():
    data = valid_action_group_data()
    data["action_group"]["steps"][1]["id"] = "lookup_incident_reference"

    with pytest.raises(ActionGroupValidationError, match="duplicate step id"):
        ActionGroup.from_dict(data)


def test_action_group_rejects_duplicate_step_orders():
    data = valid_action_group_data()
    data["action_group"]["steps"][1]["order"] = 1

    with pytest.raises(ActionGroupValidationError, match="duplicate step order"):
        ActionGroup.from_dict(data)


def test_action_group_rejects_condition_without_conditions():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["start_condition"]["conditions"] = []

    with pytest.raises(ActionGroupValidationError, match="requires at least one condition"):
        ActionGroup.from_dict(data)


def test_action_group_rejects_mapping_without_target():
    data = valid_action_group_data()
    del data["action_group"]["steps"][3]["mapped_fields"][0]["target"]

    with pytest.raises(ActionGroupValidationError, match="requires non-empty string 'target'"):
        ActionGroup.from_dict(data)
