from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.action_field_catalog import (
    ActionFieldCatalog,
    ActionFieldCatalogValidationError,
)


def valid_field_catalog_data():
    return {
        "action_field_catalog": {
            "fields": [
                "sncIncident.State",
                "insights.Escalation",
                "alert.alertDetails.alertState",
            ],
            "wildcard_prefixes": [
                "insights.extra.",
            ],
        }
    }


def test_action_field_catalog_from_dict_builds_model():
    catalog = ActionFieldCatalog.from_dict(valid_field_catalog_data())

    assert catalog.has_field("sncIncident.State") is True
    assert catalog.has_field("insights.extra.Edwin_Incident_Auto_Close") is True
    assert catalog.has_field("sncIncident.Unknown") is False


def test_action_field_catalog_to_dict_round_trips_shape():
    catalog = ActionFieldCatalog.from_dict(valid_field_catalog_data())

    assert catalog.to_dict() == valid_field_catalog_data()


def test_action_field_catalog_rejects_duplicate_fields():
    data = valid_field_catalog_data()
    data["action_field_catalog"]["fields"].append("sncIncident.State")

    with pytest.raises(ActionFieldCatalogValidationError, match="duplicate field"):
        ActionFieldCatalog.from_dict(data)


def test_action_field_catalog_rejects_duplicate_wildcard_prefixes():
    data = valid_field_catalog_data()
    data["action_field_catalog"]["wildcard_prefixes"].append("insights.extra.")

    with pytest.raises(ActionFieldCatalogValidationError, match="duplicate wildcard prefix"):
        ActionFieldCatalog.from_dict(data)
