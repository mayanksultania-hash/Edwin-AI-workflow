from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.action_group_validator import (
    ActionGroupValidator,
    ActionGroupValidatorError,
    validate_action_group_with_context,
)
from ai_workflow.mcp.action_ui_context import build_default_action_ui_context
from ai_workflow.models.action_group import ActionGroup
from test_action_group_model import valid_action_group_data


def build_validator() -> ActionGroupValidator:
    return ActionGroupValidator.from_context(build_default_action_ui_context())


def test_action_group_validator_accepts_incident_processing_ui_shape():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    build_validator().validate(action_group)


def test_validate_action_group_with_context_accepts_incident_processing_ui_shape():
    action_group = ActionGroup.from_dict(valid_action_group_data())

    validate_action_group_with_context(
        action_group=action_group,
        context=build_default_action_ui_context(),
    )


def test_action_group_validator_rejects_unknown_general_source():
    data = valid_action_group_data()
    data["action_group"]["source"] = "unknownSource"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="General source"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_action_type():
    data = valid_action_group_data()
    data["action_group"]["steps"][1]["action_type"] = "Update Something Else"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown action type"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_invalid_group_condition_operator():
    data = valid_action_group_data()
    data["action_group"]["group_condition"]["operator"] = "SOME_GROUP_OPERATOR"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Group condition group operator"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_group_condition_field():
    data = valid_action_group_data()
    data["action_group"]["group_condition"]["conditions"][0]["field"] = "Unknown Field"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Group condition field"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_config_field():
    data = valid_action_group_data()
    data["action_group"]["steps"][2]["config"]["delay_seconds"] = 300
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Action Config"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_missing_required_config():
    data = valid_action_group_data()
    data["action_group"]["steps"][2]["config"] = {}
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="missing required Action Config"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_invalid_stop_outcome():
    data = valid_action_group_data()
    data["action_group"]["steps"][4]["stop_condition"] = {
        "operator": "OR",
        "conditions": [
            {
                "record": "action_outcome",
                "field": "outcome",
                "operator": "EQUALS",
                "value": "Done",
            }
        ],
    }
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Stop condition outcome"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_invalid_condition_operator():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["start_condition"]["conditions"][0]["operator"] = "Around"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Start Condition operator"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_start_condition_field():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["start_condition"]["conditions"][0]["field"] = (
        "Unknown Field"
    )
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Start Condition field"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_invalid_mapping_type():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["mapped_fields"][0]["mappings"][0]["type"] = "magic"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Mapped Fields type"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_mapped_field_target():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["mapped_fields"][0]["target"] = "Unknown Field"
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Mapped Fields target field"):
        build_validator().validate(action_group)


def test_action_group_validator_rejects_unknown_mapping_variable():
    data = valid_action_group_data()
    data["action_group"]["steps"][3]["mapped_fields"][0]["mappings"][0] = {
        "type": "variable",
        "value": "sncIncident.Unknown Field",
    }
    action_group = ActionGroup.from_dict(data)

    with pytest.raises(ActionGroupValidatorError, match="unknown Mapped Fields variable field"):
        build_validator().validate(action_group)
