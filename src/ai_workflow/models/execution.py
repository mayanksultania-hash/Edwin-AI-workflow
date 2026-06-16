"""Execution models for workflow runs."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class StepExecution:
    step_id: str
    tool: str
    action: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass(frozen=True)
class WorkflowExecution:
    workflow_name: str
    success: bool
    steps: tuple[StepExecution, ...]
    final_data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
