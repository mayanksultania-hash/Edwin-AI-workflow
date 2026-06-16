"""Shared constants for the AI workflow project."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "workflow_config.yaml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
VERSION_FILE_PATH = PROJECT_ROOT / "VERSION"
DEFAULT_AUDIT_DIR = PROJECT_ROOT / "outputs" / "audit"
DEFAULT_GENERATED_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "generated"

DEFAULT_OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
SUPPORTED_LANGUAGES = ("python", "typescript")
SUPPORTED_EXECUTION_MODES = ("mock",)
DEFAULT_WORKFLOW_VERSION = "v0.1"
