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
    action_catalog_source: str = "static"
    action_catalog_base_url: str | None = None
    action_catalog_auth_token_env_var: str | None = None
    action_catalog_timeout_seconds: float = 10.0
    action_fields_source: str = "static"
    action_fields_paths: tuple[str, ...] = ()
    action_fields_extra_fields: tuple[str, ...] = ()
    action_fields_wildcard_prefixes: tuple[str, ...] = ()
    action_service_submit_mode: str = "disabled"
    action_service_base_url: str | None = None
    action_service_submit_endpoint: str = "/action/group"
    action_service_auth_token_env_var: str | None = None
    action_service_timeout_seconds: float = 10.0
