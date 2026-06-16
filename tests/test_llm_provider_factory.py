from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.config.models import WorkflowConfig
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.llm.openai_provider import OpenAILLMProvider
from ai_workflow.llm.provider_factory import build_llm_provider


def config_with_provider(provider):
    return WorkflowConfig(
        model_provider=provider,
        model_name="mock-workflow-model",
        model_api_key_env_var="OPENAI_API_KEY",
        model_max_output_tokens=1000,
        output_language="python",
        workflow_version="v0.1",
        execution_mode="mock",
        enabled_tools=("event_tool",),
    )


def test_build_llm_provider_returns_mock_provider():
    provider = build_llm_provider(config_with_provider("mock"))

    assert isinstance(provider, MockLLMProvider)


def test_build_llm_provider_returns_openai_provider():
    provider = build_llm_provider(config_with_provider("openai"))

    assert isinstance(provider, OpenAILLMProvider)
    assert provider.api_key_env_var == "OPENAI_API_KEY"


def test_build_llm_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        build_llm_provider(config_with_provider("unknown"))
