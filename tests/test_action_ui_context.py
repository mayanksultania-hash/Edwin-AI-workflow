from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.mcp.action_catalog_context import StaticActionCatalogSource
from ai_workflow.mcp.action_field_catalog_context import StaticActionFieldCatalogSource
from ai_workflow.mcp.action_ui_context import (
    build_action_ui_context,
    build_default_action_ui_context,
)


def test_default_action_ui_context_has_sources_from_action_ui():
    context = build_default_action_ui_context()

    assert "events" in context.source_types
    assert "alerts" in context.source_types
    assert "insights" in context.source_types
    assert "sncIncident" in context.source_types
    assert "ansiblePlaybook" in context.source_types
    assert "aiGeneratedPlaybook" in context.source_types
    assert "jsonResponse" in context.source_types


def test_default_action_ui_context_has_condition_operator_keys_and_labels():
    context = build_default_action_ui_context()

    assert "AND" in context.condition_operator_keys
    assert "OR" in context.condition_operator_keys
    assert "EQUALS" in context.condition_operator_keys
    assert "NOT_EQUALS" in context.condition_operator_keys
    assert "GREATER_THAN" in context.condition_operator_keys
    assert "NOT_EMPTY" in context.condition_operator_keys

    assert "EQUALS (Equals)" in context.condition_operator_prompt_lines
    assert "NOT_EQUALS (Not equals)" in context.condition_operator_prompt_lines
    assert "NOT_EMPTY (Not empty)" in context.condition_operator_prompt_lines


def test_default_action_ui_context_has_mapping_types_from_action_ui():
    context = build_default_action_ui_context()

    assert context.mapping_types == (
        "value",
        "variable",
        "multi_variable",
        "increment_value",
    )


def test_default_action_ui_context_includes_action_catalog():
    context = build_default_action_ui_context()

    assert context.catalog.has_action("Update Insight")
    assert context.catalog.has_action("Update Alert")
    assert context.catalog.has_action("Update SNC Incident")
    assert context.catalog.has_action("Delay Action Execution")


def test_default_action_ui_context_includes_field_catalog():
    context = build_default_action_ui_context()

    assert context.field_catalog.has_field("sncIncident.State")
    assert context.field_catalog.has_field("alert.alertDetails.alertState")
    assert context.field_catalog.has_field("insights.extra.Edwin_Incident_Auto_Close")
    assert not context.field_catalog.has_field("sncIncident.NotARealField")


def test_build_action_ui_context_accepts_catalog_source():
    source = StaticActionCatalogSource(
        catalog_data={
            "action_catalog": {
                "actions": [
                    {
                        "action_name": "Org Specific Action",
                        "action_id": "real-action-id",
                        "record_type": "events",
                        "outcomes": ["Done"],
                    }
                ]
            }
        }
    )

    context = build_action_ui_context(catalog_source=source)

    assert context.catalog.has_action("Org Specific Action")
    assert context.catalog.get_action("Org Specific Action").action_id == "real-action-id"
    assert not context.catalog.has_action("Update Insight")


def test_build_action_ui_context_accepts_field_catalog_source():
    source = StaticActionFieldCatalogSource(
        catalog_data={
            "action_field_catalog": {
                "fields": ["customSource.Custom Field"],
                "wildcard_prefixes": ["customSource.extra."],
            }
        }
    )

    context = build_action_ui_context(field_catalog_source=source)

    assert context.field_catalog.has_field("customSource.Custom Field")
    assert context.field_catalog.has_field("customSource.extra.Dynamic")
    assert not context.field_catalog.has_field("sncIncident.State")
