from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.config.models import WorkflowConfig
from ai_workflow.mcp.action_catalog_context import (
    HttpActionCatalogSource,
    StaticActionCatalogSource,
)
from ai_workflow.mcp.action_catalog_source_factory import (
    build_action_catalog_source,
    build_action_field_catalog_source,
    build_action_service_submitter,
)
from ai_workflow.mcp.action_field_catalog_context import (
    FileActionFieldCatalogSource,
    StaticActionFieldCatalogSource,
)
from ai_workflow.mcp.action_service_submitter import (
    DisabledActionServiceSubmitter,
    HttpActionServiceSubmitter,
)


def sample_config(**overrides):
    values = {
        "model_provider": "mock",
        "model_name": "mock-workflow-model",
        "model_api_key_env_var": "OPENAI_API_KEY",
        "model_max_output_tokens": None,
        "output_language": "python",
        "workflow_version": "v0.1",
        "execution_mode": "mock",
        "enabled_tools": (),
        "action_catalog_source": "static",
        "action_catalog_base_url": None,
        "action_catalog_auth_token_env_var": None,
        "action_catalog_timeout_seconds": 10.0,
        "action_fields_source": "static",
        "action_fields_paths": (),
        "action_fields_extra_fields": (),
        "action_fields_wildcard_prefixes": (),
        "action_service_submit_mode": "disabled",
        "action_service_base_url": None,
        "action_service_submit_endpoint": "/action/group",
        "action_service_auth_token_env_var": None,
        "action_service_timeout_seconds": 10.0,
    }
    values.update(overrides)
    return WorkflowConfig(**values)


def test_build_action_catalog_source_returns_static_source_by_default():
    source = build_action_catalog_source(sample_config())

    assert isinstance(source, StaticActionCatalogSource)


def test_build_action_catalog_source_returns_http_source_without_auth():
    source = build_action_catalog_source(
        sample_config(
            action_catalog_source="http",
            action_catalog_base_url="http://action:8447",
            action_catalog_timeout_seconds=2.5,
        )
    )

    assert isinstance(source, HttpActionCatalogSource)
    assert source.base_url == "http://action:8447"
    assert source.headers == {}
    assert source.timeout_seconds == 2.5


def test_build_action_catalog_source_reads_auth_token_from_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("ACTION_SERVICE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.delenv("ACTION_SERVICE_TOKEN", raising=False)

    source = build_action_catalog_source(
        sample_config(
            action_catalog_source="http",
            action_catalog_base_url="http://action:8447",
            action_catalog_auth_token_env_var="ACTION_SERVICE_TOKEN",
        ),
        env_path=env_path,
    )

    assert isinstance(source, HttpActionCatalogSource)
    assert source.headers == {"Authorization": "Bearer file-token"}


def test_build_action_catalog_source_prefers_process_env_token(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("ACTION_SERVICE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setenv("ACTION_SERVICE_TOKEN", "process-token")

    source = build_action_catalog_source(
        sample_config(
            action_catalog_source="http",
            action_catalog_base_url="http://action:8447",
            action_catalog_auth_token_env_var="ACTION_SERVICE_TOKEN",
        ),
        env_path=env_path,
    )

    assert isinstance(source, HttpActionCatalogSource)
    assert source.headers == {"Authorization": "Bearer process-token"}


def test_build_action_catalog_source_requires_http_base_url():
    with pytest.raises(ValueError, match="action_catalog.base_url"):
        build_action_catalog_source(sample_config(action_catalog_source="http"))


def test_build_action_field_catalog_source_returns_static_source_by_default():
    source = build_action_field_catalog_source(sample_config())

    assert isinstance(source, StaticActionFieldCatalogSource)


def test_build_action_field_catalog_source_returns_file_source():
    source = build_action_field_catalog_source(
        sample_config(
            action_fields_source="file",
            action_fields_paths=("global_fields.json",),
            action_fields_extra_fields=("org.extra.Fixed",),
            action_fields_wildcard_prefixes=("org.extra.",),
        )
    )

    assert isinstance(source, FileActionFieldCatalogSource)
    assert source.paths == (Path("global_fields.json"),)
    assert source.extra_fields == ("org.extra.Fixed",)
    assert source.wildcard_prefixes == ("org.extra.",)


def test_build_action_field_catalog_source_requires_file_paths():
    with pytest.raises(ValueError, match="action_fields.paths"):
        build_action_field_catalog_source(sample_config(action_fields_source="file"))


def test_build_action_service_submitter_returns_disabled_by_default():
    submitter = build_action_service_submitter(sample_config())

    assert isinstance(submitter, DisabledActionServiceSubmitter)


def test_build_action_service_submitter_returns_http_submitter_without_auth():
    submitter = build_action_service_submitter(
        sample_config(
            action_service_submit_mode="http",
            action_service_base_url="http://action:8447",
            action_service_submit_endpoint="/action/group",
            action_service_timeout_seconds=2.5,
        )
    )

    assert isinstance(submitter, HttpActionServiceSubmitter)
    assert submitter.base_url == "http://action:8447"
    assert submitter.endpoint_path == "/action/group"
    assert submitter.headers == {}
    assert submitter.timeout_seconds == 2.5


def test_build_action_service_submitter_reads_auth_token_from_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("ACTION_SERVICE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.delenv("ACTION_SERVICE_TOKEN", raising=False)

    submitter = build_action_service_submitter(
        sample_config(
            action_service_submit_mode="http",
            action_service_base_url="http://action:8447",
            action_service_auth_token_env_var="ACTION_SERVICE_TOKEN",
        ),
        env_path=env_path,
    )

    assert isinstance(submitter, HttpActionServiceSubmitter)
    assert submitter.headers == {"Authorization": "Bearer file-token"}
