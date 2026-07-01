"""Constants and default paths for LM Alert Processing customization."""

from pathlib import Path

LM_ALERT_PROCESSING_BASE_ACTION_GROUP_ID = "1524b557-04e2-11ec-ad8c-0dc5c8845aca"
# parents[5]: constants.py → config/ → lm_alert_processing/ → action_groups/ → ai_workflow/ → src/ → project root
DEFAULT_BASE_YAML_PATH = (
    Path(__file__).resolve().parents[5] / "inputs" / "lm_alert_processing_base.yaml"
)
FILTER_SCHEMA_NAME = "filterCondition"
FILTER_SCHEMA_VERSION = 4
SUPPORTED_FILTER_OPERATORS = {
    "CONTAINS",
    "EQUALS",
    "EMPTY",
    "NOT_EQUALS",
    "NOT_EMPTY",
    "NOT_CONTAINS",
    "GREATER_THAN",
    "GREATER_THAN_EQUAL",
    "LESS_THAN",
    "LESS_THAN_EQUAL",
    "IN",
    "NOT_IN",
    "OLDER_THAN",
}
SERVICE_NOW_MAPPING_FIELDS = {
    "assignment_group",
    "caller_id",
    "category",
    "close_code",
    "close_notes",
    "impact",
    "priority",
    "resolved_by",
    "short_description",
    "state",
    "subcategory",
    "urgency",
    "work_notes",
}
ALLOWED_SNC_MAPPING_TARGETS = SERVICE_NOW_MAPPING_FIELDS | {
    "cmdb_ci",
    "contact_type",
    "description",
}
SNC_MAPPING_PATCH_STEP_NAMES = {
    "Create ServiceNow Incident for this alert",
    "Create ServiceNow Incident for this insight",
    "Update ServiceNow Incident linked to this alert",
    "Update ServiceNow Incident linked to this insight",
}
STEPS_WITHOUT_MAPPINGS = {
    "Find a LM-DX reference for this alert",
    "Find a LM-DX reference for this insight",
}
OLDER_THAN_TIME_UNITS = {
    "hour",
    "hours",
    "minute",
    "minutes",
    "second",
    "seconds",
    "day",
    "days",
}
OLDER_THAN_TIME_UNIT_SINGULAR = {
    "hours": "hour",
    "minutes": "minute",
    "seconds": "second",
    "days": "day",
}
CREATE_INCIDENT_STEP_REQUIRED_LAST_OUTCOMES = {
    "Create ServiceNow Incident for this alert": "Alert updated",
    "Create ServiceNow Incident for this insight": "Insight updated",
}
SUPPORTED_PATCH_TYPES = {
    "add_step_precondition_conditions",
    "remove_step",
    "set_action_config_value",
    "set_delay_seconds",
    "set_group_description",
    "set_group_name",
    "set_mapping_value",
    "set_step_precondition",
}
MIN_ACTION_GROUP_STEPS = 1
