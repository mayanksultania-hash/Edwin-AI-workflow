from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.config.loader import load_config, load_version, load_yaml_config


def write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_yaml_config_reads_file(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-model
""",
    )

    config = load_yaml_config(config_path)

    assert config["model"]["provider"] == "mock"
    assert config["model"]["name"] == "mock-model"


def test_load_yaml_config_fails_when_file_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_yaml_config(tmp_path / "missing.yaml")


def test_load_version_reads_version_file(tmp_path):
    version_path = write_file(tmp_path / "VERSION", "v1.2\n")

    assert load_version(version_path) == "v1.2"


def test_load_version_uses_default_when_file_is_missing(tmp_path):
    assert load_version(tmp_path / "VERSION") == "v0.1"


def test_load_config_returns_workflow_config(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
  name: mock-workflow-model
  max_output_tokens: 900
generation:
  output_language: typescript
execution:
  mode: mock
tools:
  enabled:
    - event_tool
    - alert_tool
""",
    )
    version_path = write_file(tmp_path / "VERSION", "v0.2\n")

    config = load_config(config_path=config_path, version_path=version_path)

    assert config.model_provider == "mock"
    assert config.model_name == "mock-workflow-model"
    assert config.model_max_output_tokens == 900
    assert config.output_language == "typescript"
    assert config.workflow_version == "v0.2"
    assert config.execution_mode == "mock"
    assert config.enabled_tools == ("event_tool", "alert_tool")
    assert config.action_catalog_source == "static"
    assert config.action_catalog_base_url is None
    assert config.action_catalog_auth_token_env_var is None
    assert config.action_catalog_timeout_seconds == 10.0
    assert config.action_fields_source == "static"
    assert config.action_fields_paths == ()
    assert config.action_fields_extra_fields == ()
    assert config.action_fields_wildcard_prefixes == ()
    assert config.action_service_submit_mode == "disabled"
    assert config.action_service_base_url is None
    assert config.action_service_submit_endpoint == "/action/group"
    assert config.action_service_auth_token_env_var is None
    assert config.action_service_timeout_seconds == 10.0


def test_load_config_reads_http_action_catalog_config(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
generation:
  output_language: python
execution:
  mode: mock
action_catalog:
  source: http
  base_url: http://action:8447
  auth_token_env_var: ACTION_SERVICE_TOKEN
  timeout_seconds: 2.5
tools:
  enabled:
""",
    )

    config = load_config(config_path=config_path, version_path=tmp_path / "VERSION")

    assert config.action_catalog_source == "http"
    assert config.action_catalog_base_url == "http://action:8447"
    assert config.action_catalog_auth_token_env_var == "ACTION_SERVICE_TOKEN"
    assert config.action_catalog_timeout_seconds == 2.5


def test_load_config_reads_file_action_fields_config(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
generation:
  output_language: python
execution:
  mode: mock
action_fields:
  source: file
  paths:
    - /tmp/global_fields.json
  extra_fields:
    - orgRecord.extra.Fixed
  wildcard_prefixes:
    - orgRecord.extra.
tools:
  enabled:
""",
    )

    config = load_config(config_path=config_path, version_path=tmp_path / "VERSION")

    assert config.action_fields_source == "file"
    assert config.action_fields_paths == ("/tmp/global_fields.json",)
    assert config.action_fields_extra_fields == ("orgRecord.extra.Fixed",)
    assert config.action_fields_wildcard_prefixes == ("orgRecord.extra.",)


def test_load_config_reads_http_action_service_submit_config(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  provider: mock
generation:
  output_language: python
execution:
  mode: mock
action_service:
  submit_mode: http
  base_url: http://action:8447
  submit_endpoint: /action/group
  auth_token_env_var: ACTION_SERVICE_TOKEN
  timeout_seconds: 2.5
tools:
  enabled:
""",
    )

    config = load_config(config_path=config_path, version_path=tmp_path / "VERSION")

    assert config.action_service_submit_mode == "http"
    assert config.action_service_base_url == "http://action:8447"
    assert config.action_service_submit_endpoint == "/action/group"
    assert config.action_service_auth_token_env_var == "ACTION_SERVICE_TOKEN"
    assert config.action_service_timeout_seconds == 2.5


def test_load_config_rejects_unsupported_language(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: ruby
execution:
  mode: mock
""",
    )

    with pytest.raises(ValueError, match="Unsupported output language"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_unsupported_execution_mode(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: real
""",
    )

    with pytest.raises(ValueError, match="Unsupported execution mode"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_invalid_max_output_tokens(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
model:
  max_output_tokens: 0
generation:
  output_language: python
execution:
  mode: mock
""",
    )

    with pytest.raises(ValueError, match="model.max_output_tokens"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_unsupported_action_catalog_source(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: mock
action_catalog:
  source: database
""",
    )

    with pytest.raises(ValueError, match="Unsupported action catalog source"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_invalid_action_catalog_timeout(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: mock
action_catalog:
  timeout_seconds: 0
""",
    )

    with pytest.raises(ValueError, match="action_catalog.timeout_seconds"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_unsupported_action_fields_source(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: mock
action_fields:
  source: database
""",
    )

    with pytest.raises(ValueError, match="Unsupported action fields source"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_rejects_unsupported_action_service_submit_mode(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: mock
action_service:
  submit_mode: database
""",
    )

    with pytest.raises(ValueError, match="Unsupported action service submit mode"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")


def test_load_config_requires_action_service_base_url_for_http_submit(tmp_path):
    config_path = write_file(
        tmp_path / "workflow_config.yaml",
        """
generation:
  output_language: python
execution:
  mode: mock
action_service:
  submit_mode: http
""",
    )

    with pytest.raises(ValueError, match="action_service.base_url"):
        load_config(config_path=config_path, version_path=tmp_path / "VERSION")
