"""Create LLM providers from config."""

from ai_workflow.config.models import WorkflowConfig
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.llm.openai_provider import OpenAILLMProvider


def build_llm_provider(config: WorkflowConfig) -> BaseLLMProvider:
    if config.model_provider == "mock":
        return MockLLMProvider()

    if config.model_provider == "openai":
        return OpenAILLMProvider(api_key_env_var=config.model_api_key_env_var)

    raise ValueError(f"Unsupported LLM provider: {config.model_provider}")
