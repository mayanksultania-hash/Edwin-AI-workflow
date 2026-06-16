from pathlib import Path
import asyncio
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.llm.openai_provider import OpenAILLMProvider
from ai_workflow.models.llm import LLMRequest


class FakeResponses:
    def __init__(self):
        self.last_args = None

    async def create(self, **kwargs):
        self.last_args = kwargs
        return {
            "output_text": f"workflow yaml for {kwargs['input']}",
            "model": kwargs["model"],
        }


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_provider_uses_responses_api_client():
    client = FakeClient()
    response = asyncio.run(
        OpenAILLMProvider(
            api_key_env_var="OPENAI_API_KEY",
            client=client,
        ).generate(
            LLMRequest(
                prompt="create workflow",
                model_name="gpt-test",
                max_output_tokens=700,
            )
        )
    )

    assert response.text == "workflow yaml for create workflow"
    assert response.model_name == "gpt-test"
    assert response.provider == "openai"
    assert response.raw_response["model"] == "gpt-test"
    assert client.responses.last_args["max_output_tokens"] == 700


def test_openai_provider_omits_max_output_tokens_when_not_configured():
    client = FakeClient()

    asyncio.run(
        OpenAILLMProvider(
            api_key_env_var="OPENAI_API_KEY",
            client=client,
        ).generate(
            LLMRequest(
                prompt="create workflow",
                model_name="gpt-test",
            )
        )
    )

    assert "max_output_tokens" not in client.responses.last_args


def test_openai_provider_requires_api_key_when_building_client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Missing API key"):
        OpenAILLMProvider(
            api_key_env_var="OPENAI_API_KEY",
            env_path=tmp_path / ".env",
        )._build_client()
