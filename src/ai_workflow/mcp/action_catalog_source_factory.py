"""Build Action catalog sources from config."""

from pathlib import Path

from ai_workflow.config.constants import DEFAULT_ENV_PATH
from ai_workflow.config.env import get_env_value
from ai_workflow.config.models import WorkflowConfig
from ai_workflow.mcp.action_catalog_context import (
    ActionCatalogSource,
    HttpActionCatalogSource,
    build_default_action_catalog_source,
)
from ai_workflow.mcp.action_field_catalog_context import (
    ActionFieldCatalogSource,
    FileActionFieldCatalogSource,
    build_default_action_field_catalog_source,
)
from ai_workflow.mcp.action_service_submitter import (
    ActionServiceSubmitter,
    DisabledActionServiceSubmitter,
    HttpActionServiceSubmitter,
)


def build_action_catalog_source(
    config: WorkflowConfig,
    env_path: Path = DEFAULT_ENV_PATH,
) -> ActionCatalogSource:
    if config.action_catalog_source == "static":
        return build_default_action_catalog_source()

    if config.action_catalog_source == "http":
        if not config.action_catalog_base_url:
            raise ValueError("action_catalog.base_url is required when source is http")

        return HttpActionCatalogSource(
            base_url=config.action_catalog_base_url,
            headers=_build_headers(config, env_path),
            timeout_seconds=config.action_catalog_timeout_seconds,
        )

    raise ValueError(f"Unsupported action catalog source: {config.action_catalog_source}")


def build_action_field_catalog_source(config: WorkflowConfig) -> ActionFieldCatalogSource:
    if config.action_fields_source == "static":
        return build_default_action_field_catalog_source()

    if config.action_fields_source == "file":
        if not config.action_fields_paths:
            raise ValueError("action_fields.paths is required when source is file")

        return FileActionFieldCatalogSource(
            paths=tuple(Path(path) for path in config.action_fields_paths),
            extra_fields=config.action_fields_extra_fields,
            wildcard_prefixes=config.action_fields_wildcard_prefixes,
        )

    raise ValueError(f"Unsupported action fields source: {config.action_fields_source}")


def build_action_service_submitter(
    config: WorkflowConfig,
    env_path: Path = DEFAULT_ENV_PATH,
) -> ActionServiceSubmitter:
    if config.action_service_submit_mode == "disabled":
        return DisabledActionServiceSubmitter()

    if config.action_service_submit_mode == "http":
        if not config.action_service_base_url:
            raise ValueError("action_service.base_url is required when submit_mode is http")

        return HttpActionServiceSubmitter(
            base_url=config.action_service_base_url,
            endpoint_path=config.action_service_submit_endpoint,
            headers=_build_action_service_headers(config, env_path),
            timeout_seconds=config.action_service_timeout_seconds,
        )

    raise ValueError(
        f"Unsupported action service submit mode: {config.action_service_submit_mode}"
    )


def _build_headers(config: WorkflowConfig, env_path: Path) -> dict[str, str]:
    if not config.action_catalog_auth_token_env_var:
        return {}

    token = get_env_value(config.action_catalog_auth_token_env_var, env_path)
    if not token:
        return {}

    return {"Authorization": f"Bearer {token}"}


def _build_action_service_headers(config: WorkflowConfig, env_path: Path) -> dict[str, str]:
    if not config.action_service_auth_token_env_var:
        return {}

    token = get_env_value(config.action_service_auth_token_env_var, env_path)
    if not token:
        return {}

    return {"Authorization": f"Bearer {token}"}
