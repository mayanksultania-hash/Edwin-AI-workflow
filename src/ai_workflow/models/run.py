"""Run models for the AI workflow app."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ai_workflow.models.execution import WorkflowExecution
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    WorkflowPlan,
)
from ai_workflow.models.output import GeneratedOutputPaths
from ai_workflow.models.output import (
    ActionGroupOutputPaths,
    ActionServiceJsonOutputPaths,
)
from ai_workflow.models.action_group import ActionGroup
from ai_workflow.models.action_service import ActionServiceSubmitResult
from ai_workflow.models.workflow import Workflow


@dataclass(frozen=True)
class WorkflowRunResult:
    workflow: Workflow
    workflow_yaml: str
    generated_code: str
    execution: WorkflowExecution
    intent: Optional[Intent] = None
    mcp_context: Optional[MCPContext] = None
    plan: Optional[WorkflowPlan] = None
    code_verification: Optional[CodeVerification] = None
    audit_path: Optional[Path] = None
    output_paths: Optional[GeneratedOutputPaths] = None


@dataclass(frozen=True)
class ActionGroupRunResult:
    action_group: ActionGroup
    action_group_yaml: str
    action_service_json: dict
    action_group_output_paths: Optional[ActionGroupOutputPaths] = None
    action_service_json_output_paths: Optional[ActionServiceJsonOutputPaths] = None
    submit_result: Optional[ActionServiceSubmitResult] = None
