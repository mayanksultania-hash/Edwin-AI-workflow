"""Data models for validation results."""

from dataclasses import dataclass
from pathlib import Path

from ai_workflow.models.workflow import Workflow


@dataclass(frozen=True)
class WorkflowFileValidationResult:
    path: Path
    workflow: Workflow

    @property
    def step_count(self) -> int:
        return len(self.workflow.steps)
