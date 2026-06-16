"""Audit models for workflow runs."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    run_id: str
    prompt: str
    workflow_name: str
    workflow_yaml: str
    generated_code: str
    execution_success: bool
    final_data: dict[str, Any]
    created_at: str
