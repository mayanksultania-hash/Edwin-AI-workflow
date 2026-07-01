"""Models for guided Action Group customization."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GuidedQuestion:
    key: str
    question: str
    example_answer: str


@dataclass(frozen=True)
class ActionGroupCustomizationPlan:
    summary: str
    base_action_group_id: str
    target_action_group_name: str
    recommended_changes: list[dict[str, Any]] = field(default_factory=list)
    questions_used: int = 0


@dataclass(frozen=True)
class ActionGroupCustomizationResult:
    plan: ActionGroupCustomizationPlan
    final_action_group_json: dict[str, Any]
    output_path: Path
    validation_passed: bool
    validation_differences: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionGroupYamlCustomizationResult:
    questions: tuple[GuidedQuestion, ...]
    patch_summary: str
    patches: list[dict[str, Any]]
    final_yaml: str
    output_path: Path
    validation_passed: bool
    validation_errors: list[str] = field(default_factory=list)
