from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.generator.prompts import build_action_group_generation_prompt
from ai_workflow.mcp.action_ui_context import (
    ActionOperator,
    build_default_action_ui_context,
)
from ai_workflow.models.action_field_catalog import ActionFieldCatalog


def test_action_group_generation_prompt_requires_yaml_only():
    prompt = build_action_group_generation_prompt("Create incident processing action group")

    assert "Return only YAML." in prompt
    assert "Do not include markdown fences." in prompt
    assert "Do not include explanations." in prompt


def test_action_group_generation_prompt_stays_close_to_action_ui():
    prompt = build_action_group_generation_prompt("Create incident processing action group")

    assert "General, ordered Actions, Start Condition, Stop condition" in prompt
    assert "Action Config, and Mapped Fields" in prompt
    assert "Keep steps flat and ordered, like the Action UI list." in prompt


def test_action_group_generation_prompt_includes_action_ui_context():
    prompt = build_action_group_generation_prompt("Create incident processing action group")

    assert "Allowed source types:" in prompt
    assert "- sncIncident" in prompt
    assert "- insights" in prompt
    assert "- ansiblePlaybook" in prompt

    assert "Allowed action types:" in prompt
    assert "- Lookup internal rowkey" in prompt
    assert "- Update Insight" in prompt
    assert "- Delay Action Execution" in prompt
    assert "- Update SNC Incident" in prompt

    assert "Allowed condition operators:" in prompt
    assert "- EQUALS (Equals)" in prompt
    assert "- NOT_EQUALS (Not equals)" in prompt
    assert "- NOT_EMPTY (Not empty)" in prompt

    assert "Allowed mapping types:" in prompt
    assert "- value" in prompt
    assert "- variable" in prompt

    assert "Allowed field paths:" in prompt
    assert "- sncIncident.State" in prompt
    assert "- alert.alertDetails.alertState" in prompt
    assert "Allowed wildcard field prefixes:" in prompt
    assert "- insights.extra." in prompt


def test_action_group_generation_prompt_includes_full_incident_processing_pattern():
    prompt = build_action_group_generation_prompt(
        "Create an Incident Processing action group"
    )

    assert "Example 1: Incident Processing style" in prompt
    assert "Use this pattern when the user asks to process ServiceNow incident updates" in prompt
    assert "name: Incident Processing v3.0" in prompt
    assert "source: sncIncident" in prompt
    assert "id: lookup_incident_reference" in prompt
    assert "id: store_incident_details_in_insight" in prompt
    assert "id: wait_if_incident_resolved_and_insight_active" in prompt
    assert "id: reopen_incident_if_insight_state_is_active" in prompt
    assert "id: store_incident_details_in_alert" in prompt
    assert "id: wait_if_incident_resolved_and_alert_active" in prompt
    assert "id: reopen_incident_if_singleton_alert_state_is_active" in prompt
    assert "id: store_incident_details_in_additional_alerts" in prompt


def test_action_group_generation_prompt_uses_operator_keys_in_examples():
    prompt = build_action_group_generation_prompt(
        "Create an Incident Processing action group"
    )

    assert "Use condition operator keys, not UI labels." in prompt
    assert "operator: EQUALS" in prompt
    assert "operator: GREATER_THAN" in prompt
    assert "operator: NOT_EQUALS" in prompt
    assert "delay_minutes: 5" in prompt


def test_action_group_generation_prompt_includes_close_insight_pattern():
    prompt = build_action_group_generation_prompt("Close an insight")

    assert "Example 2: Close Insight style" in prompt
    assert "name: Close Insight v3.0" in prompt
    assert 'name: Set Escalation to "closed"' in prompt
    assert "config:" in prompt
    assert "add_additional_alerts: true" in prompt


def test_action_group_generation_prompt_includes_user_request():
    prompt = build_action_group_generation_prompt(
        "Create an action group for ServiceNow incident updates"
    )

    assert "User request:" in prompt
    assert "Create an action group for ServiceNow incident updates" in prompt


def test_action_group_generation_prompt_accepts_custom_context():
    context = build_default_action_ui_context()
    custom_context = type(context)(
        catalog=context.catalog,
        field_catalog=ActionFieldCatalog(fields=("customSource.Custom Field",)),
        source_types=("customSource",),
        condition_operators=(ActionOperator(key="EQUALS", label="Equals"),),
        mapping_types=("value",),
    )

    prompt = build_action_group_generation_prompt(
        user_request="Create custom action group",
        action_ui_context=custom_context,
    )

    assert "- customSource" in prompt
    assert "- EQUALS (Equals)" in prompt
    assert "- sncIncident" not in prompt
    assert "- customSource.Custom Field" in prompt
