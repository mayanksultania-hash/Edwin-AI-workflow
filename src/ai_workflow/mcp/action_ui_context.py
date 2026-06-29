"""Action UI context used by Phase 2 validation and generation."""

from dataclasses import dataclass

from ai_workflow.mcp.action_catalog_context import (
    ActionCatalogSource,
    build_default_action_catalog_source,
)
from ai_workflow.mcp.action_field_catalog_context import (
    ActionFieldCatalogSource,
    build_default_action_field_catalog_source,
)
from ai_workflow.models.action_catalog import ActionCatalog
from ai_workflow.models.action_field_catalog import ActionFieldCatalog


DEFAULT_SOURCE_TYPES = (
    "aiGeneratedPlaybook",
    "alerts",
    "ansiblePlaybook",
    "bigPandaIncident",
    "bmcHelixIncident",
    "connectWiseTicket",
    "dynamicsIncident",
    "emailMessage",
    "events",
    "freshServiceTicket",
    "insights",
    "jiraIssue",
    "jsonResponse",
    "ml",
    "msTeamsMessage",
    "pagerdutyIncident",
    "rundeckJob",
    "slackMessage",
    "sncCase",
    "sncCmdb",
    "sncIncident",
    "xMattersIncident",
    "zendeskTicket",
)


@dataclass(frozen=True)
class ActionOperator:
    key: str
    label: str


DEFAULT_CONDITION_OPERATORS = (
    ActionOperator(key="AND", label="AND"),
    ActionOperator(key="OR", label="OR"),
    ActionOperator(key="EQUALS", label="Equals"),
    ActionOperator(key="NOT_EQUALS", label="Not equals"),
    ActionOperator(key="GREATER_THAN", label="Greater than"),
    ActionOperator(key="LESS_THAN", label="Less than"),
    ActionOperator(key="GREATER_THAN_OR_EQUALS", label="Greater than or equals"),
    ActionOperator(key="LESS_THAN_OR_EQUALS", label="Less than or equals"),
    ActionOperator(key="NOT_EMPTY", label="Not empty"),
    ActionOperator(key="EMPTY", label="Empty"),
    ActionOperator(key="CONTAINS", label="Contains"),
    ActionOperator(key="NOT_CONTAINS", label="Not contains"),
)

DEFAULT_MAPPING_TYPES = (
    "value",
    "variable",
    "multi_variable",
    "increment_value",
)

@dataclass(frozen=True)
class ActionUiContext:
    catalog: ActionCatalog
    field_catalog: ActionFieldCatalog
    source_types: tuple[str, ...]
    condition_operators: tuple[ActionOperator, ...]
    mapping_types: tuple[str, ...]

    @property
    def condition_operator_keys(self) -> tuple[str, ...]:
        return tuple(operator.key for operator in self.condition_operators)

    @property
    def condition_operator_prompt_lines(self) -> tuple[str, ...]:
        return tuple(
            f"{operator.key} ({operator.label})"
            for operator in self.condition_operators
        )


def build_action_ui_context(
    catalog_source: ActionCatalogSource | None = None,
    field_catalog_source: ActionFieldCatalogSource | None = None,
) -> ActionUiContext:
    action_source = catalog_source or build_default_action_catalog_source()
    field_source = field_catalog_source or build_default_action_field_catalog_source()
    return ActionUiContext(
        catalog=action_source.load_catalog(),
        field_catalog=field_source.load_catalog(),
        source_types=DEFAULT_SOURCE_TYPES,
        condition_operators=DEFAULT_CONDITION_OPERATORS,
        mapping_types=DEFAULT_MAPPING_TYPES,
    )


def build_default_action_ui_context() -> ActionUiContext:
    return build_action_ui_context()
