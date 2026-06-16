"""Validate workflows before execution."""

from dataclasses import dataclass

from ai_workflow.engine.reference_validator import validate_workflow_references
from ai_workflow.models.workflow import Workflow
from ai_workflow.tools.registry import ToolRegistry


class WorkflowToolValidationError(ValueError):
    """Raised when workflow tools or actions are not valid."""


@dataclass(frozen=True)
class WorkflowValidator:
    registry: ToolRegistry

    def validate(self, workflow: Workflow) -> None:
        validate_workflow_tools(workflow=workflow, registry=self.registry)
        validate_workflow_references(workflow)


def validate_workflow_tools(workflow: Workflow, registry: ToolRegistry) -> None:
    for step in workflow.steps:
        try:
            tool = registry.get(step.tool)
        except KeyError as error:
            raise WorkflowToolValidationError(
                f"Step '{step.id}' uses unknown tool '{step.tool}'"
            ) from error

        if step.action not in tool.supported_actions:
            raise WorkflowToolValidationError(
                f"Step '{step.id}' uses unsupported action '{step.action}' "
                f"for tool '{step.tool}'"
            )
