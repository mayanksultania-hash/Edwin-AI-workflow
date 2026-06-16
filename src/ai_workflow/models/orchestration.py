"""Data models for workflow orchestration."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Intent:
    name: str
    domain: str
    summary: str
    entities: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPContext:
    source: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    order: int
    goal: str
    tool: str
    action: str
    inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowPlan:
    intent: Intent
    steps: tuple[PlanStep, ...]

    def summary_lines(self) -> list[str]:
        return [
            f"{step.order}. {step.goal} using {step.tool}.{step.action}"
            for step in self.steps
        ]


@dataclass(frozen=True)
class CodeVerification:
    approved: bool
    risk_level: str
    summary: str
    issues: tuple[str, ...] = ()
