"""Load config and version values for the AI workflow project."""

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

from ai_workflow.config.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_OPENAI_API_KEY_ENV,
    DEFAULT_WORKFLOW_VERSION,
    SUPPORTED_EXECUTION_MODES,
    SUPPORTED_LANGUAGES,
    VERSION_FILE_PATH,
)
from ai_workflow.config.models import WorkflowConfig


def load_yaml_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    content = config_path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(content) or {}

    return _load_simple_yaml(content)


def _load_simple_yaml(content: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    current_list_key: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            current_list_key = None
            data[current_section] = {}
            continue

        if current_section is None:
            continue

        section = data[current_section]
        if stripped.endswith(":"):
            current_list_key = stripped[:-1]
            section[current_list_key] = []
            continue

        if stripped.startswith("- ") and current_list_key:
            section[current_list_key].append(stripped[2:].strip())
            continue

        if ":" in stripped:
            key, value = stripped.split(":", 1)
            section[key.strip()] = value.strip()

    return data


def load_version(version_path: Path = VERSION_FILE_PATH) -> str:
    if not version_path.exists():
        return DEFAULT_WORKFLOW_VERSION

    version = version_path.read_text(encoding="utf-8").strip()
    return version or DEFAULT_WORKFLOW_VERSION


def load_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
    version_path: Path = VERSION_FILE_PATH,
) -> WorkflowConfig:
    raw_config = load_yaml_config(config_path)
    version = load_version(version_path)

    model_config = raw_config.get("model", {})
    output_language = raw_config.get("generation", {}).get("output_language", "python")
    execution_mode = raw_config.get("execution", {}).get("mode", "mock")
    max_output_tokens = _optional_positive_int(
        model_config.get("max_output_tokens"),
        "model.max_output_tokens",
    )

    if output_language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported output language: {output_language}")

    if execution_mode not in SUPPORTED_EXECUTION_MODES:
        raise ValueError(f"Unsupported execution mode: {execution_mode}")

    return WorkflowConfig(
        model_provider=model_config.get("provider", "mock"),
        model_name=model_config.get("name", "mock-workflow-model"),
        model_api_key_env_var=model_config.get(
            "api_key_env_var",
            DEFAULT_OPENAI_API_KEY_ENV,
        ),
        model_max_output_tokens=max_output_tokens,
        output_language=output_language,
        workflow_version=version,
        execution_mode=execution_mode,
        enabled_tools=tuple(raw_config.get("tools", {}).get("enabled", [])),
    )


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None

    try:
        int_value = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a positive integer") from error

    if int_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")

    return int_value
