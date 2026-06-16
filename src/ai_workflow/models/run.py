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
