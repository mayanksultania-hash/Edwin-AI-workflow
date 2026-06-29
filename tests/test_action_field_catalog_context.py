from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.mcp.action_field_catalog_context import (
    ActionFieldCatalogSourceError,
    FileActionFieldCatalogSource,
    StaticActionFieldCatalogSource,
    build_default_action_field_catalog,
    build_default_action_field_catalog_source,
)


def test_static_action_field_catalog_source_loads_catalog():
    source = StaticActionFieldCatalogSource(
        catalog_data={
            "action_field_catalog": {
                "fields": ["sncIncident.State"],
                "wildcard_prefixes": ["sncIncident.extra."],
            }
        }
    )

    catalog = source.load_catalog()

    assert catalog.has_field("sncIncident.State")
    assert catalog.has_field("sncIncident.extra.Custom")


def test_default_action_field_catalog_source_matches_default_catalog():
    source_catalog = build_default_action_field_catalog_source().load_catalog()
    default_catalog = build_default_action_field_catalog()

    assert source_catalog.to_dict() == default_catalog.to_dict()


def test_file_action_field_catalog_source_loads_global_fields_json(tmp_path):
    path = tmp_path / "global_fields.json"
    path.write_text(
        """
{
  "records": [
    {
      "recordType": "events",
      "fields": [
        {"name": "cf.eventName"},
        {"name": "meta.eventType"}
      ]
    },
    {
      "recordType": "alerts",
      "fields": [
        {"name": "alertDetails.alertState"}
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    catalog = FileActionFieldCatalogSource(paths=(path,)).load_catalog()

    assert catalog.has_field("events.cf.eventName")
    assert catalog.has_field("events.meta.eventType")
    assert catalog.has_field("alerts.alertDetails.alertState")
    assert catalog.has_field("alert.alertDetails.alertState")
    assert catalog.has_field("sncIncident.State")
    assert catalog.has_field("insights.extra.Edwin_Incident_Auto_Close")


def test_file_action_field_catalog_source_merges_extra_fields_and_prefixes(tmp_path):
    path = tmp_path / "fields.json"
    path.write_text('["customSource.Custom Field"]', encoding="utf-8")

    catalog = FileActionFieldCatalogSource(
        paths=(path,),
        extra_fields=("orgRecord.extra.Fixed",),
        wildcard_prefixes=("orgRecord.extra.",),
    ).load_catalog()

    assert catalog.has_field("customSource.Custom Field")
    assert catalog.has_field("orgRecord.extra.Fixed")
    assert catalog.has_field("orgRecord.extra.Dynamic")


def test_file_action_field_catalog_source_rejects_missing_file(tmp_path):
    source = FileActionFieldCatalogSource(paths=(tmp_path / "missing.json",))

    with pytest.raises(ActionFieldCatalogSourceError, match="Field catalog file not found"):
        source.load_catalog()
