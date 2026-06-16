"""Config models for the AI workflow project."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowConfig:
    model_provider: str
    model_name: str
    model_api_key_env_var: str
    model_max_output_tokens: int | None
    output_language: str
    workflow_version: str
    execution_mode: str
    enabled_tools: tuple[str, ...]
