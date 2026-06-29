from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.action_group_yaml import (
    dump_action_group_yaml,
    load_action_group_yaml,
    load_action_group_yaml_file,
    write_action_group_yaml_file,
)
from ai_workflow.models.action_group import ActionGroup
from test_action_group_model import valid_action_group_data


ACTION_GROUP_YAML = """
action_group:
  name: Incident Processing v3.0
  description: Default action group to process ServiceNow incident updates sent from the LM-DX application
  source: sncIncident
  rule:
  group_condition:
    operator: EQUALS
    conditions:
      - record: sncIncident
        field: State
        operator: EQUALS
        value: Resolved
  steps:
    - order: 1
      id: lookup_incident_reference
      action_type: Lookup internal rowkey
      name: Lookup Incident reference
      description: Lookup Incident reference
    - order: 2
      id: store_incident_details_in_insight
      action_type: Update Insight
      name: Store Incident details in Insight
      description: Store Incident details in Insight
    - order: 3
      id: wait_if_incident_resolved_and_insight_active
      action_type: Delay Action Execution
      name: Wait for 5 min if Incident is Resolved and Insight is Active
      description: Wait for 5 min if Incident is Resolved and Insight is Active
      config:
        delay_minutes: 5
    - order: 4
      id: reopen_incident_if_insight_active
      action_type: Update SNC Incident
      name: Re-open Incident If Insight State is Active
      description: Re-open Incident If Insight State is Active
      start_condition:
        operator: AND
        conditions:
          - record: actionsystem
            field: Last Action Outcome
            operator: EQUALS
            value: Delay Completed
          - record: sncIncident
            field: State
            operator: EQUALS
            value: Resolved
          - record: insights
            field: State
            operator: EQUALS
            value: active
          - record: insights
            field: Severity
            operator: GREATER_THAN
            value: Warning
          - record: insights
            field: insights.extra.Edwin_Incident_Auto...
            operator: EQUALS
            value: false
      mapped_fields:
        - target: State
          mappings:
            - type: value
              value: In Progress
    - order: 5
      id: store_incident_details_in_alert
      action_type: Update Alert
      name: Store Incident details in Alert
      description: Store Incident details in Alert
    - order: 6
      id: wait_if_incident_resolved_and_alert_active
      action_type: Delay Action Execution
      name: Wait for 5 min if Incident is Resolved and Alert is Active
      description: Wait for 5 min if Incident is Resolved and Alert is Active
      config:
        delay_minutes: 5
    - order: 7
      id: reopen_incident_if_singleton_alert_active
      action_type: Update SNC Incident
      name: Re-open Incident If Singleton Alert State is Active
      description: Re-open Incident If Singleton Alert State is Active
    - order: 8
      id: store_incident_details_in_additional_alerts
      action_type: Update Alert
      name: Store Incident details in additional Alerts
      description: Store Incident details in additional Alerts
      use_additional_records: true
"""


def test_load_action_group_yaml_builds_action_ui_shape():
    action_group = load_action_group_yaml(ACTION_GROUP_YAML)

    assert action_group.name == "Incident Processing v3.0"
    assert action_group.source == "sncIncident"
    assert action_group.rule is None
    assert action_group.group_condition is not None
    assert action_group.group_condition.conditions[0].field == "State"
    assert len(action_group.steps) == 8
    assert action_group.steps[0].action_type == "Lookup internal rowkey"
    assert action_group.steps[3].start_condition.conditions[0].record == "actionsystem"
    assert action_group.steps[3].mapped_fields[0].target == "State"
    assert action_group.steps[7].use_additional_records is True


def test_dump_action_group_yaml_writes_readable_action_ui_yaml():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    yaml_text = dump_action_group_yaml(action_group)

    assert "action_group:" in yaml_text
    assert "name: Incident Processing v3.0" in yaml_text
    assert "source: sncIncident" in yaml_text
    assert "group_condition:" in yaml_text
    assert "action_type: Update SNC Incident" in yaml_text
    assert "record: actionsystem" in yaml_text
    assert "use_additional_records: true" in yaml_text


def test_dumped_action_group_yaml_can_be_loaded_again():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    loaded_again = load_action_group_yaml(dump_action_group_yaml(action_group))

    assert loaded_again == action_group


def test_action_group_yaml_file_round_trip(tmp_path):
    action_group = ActionGroup.from_dict(valid_action_group_data())
    path = tmp_path / "incident_processing.action-group.yaml"

    write_action_group_yaml_file(action_group, path)
    loaded = load_action_group_yaml_file(path)

    assert loaded == action_group
