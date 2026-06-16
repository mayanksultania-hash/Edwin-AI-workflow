from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMRequest, LLMResponse


class FakeLLMProvider(BaseLLMProvider):
    provider_name = "fake"

    async def generate(self, request):
        return LLMResponse(
            text=f"generated: {request.prompt}",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_llm_provider_contract_returns_response():
    response = asyncio.run(
        FakeLLMProvider().generate(
            LLMRequest(
                prompt="create workflow",
                model_name="test-model",
            )
        )
    )

    assert response.text == "generated: create workflow"
    assert response.model_name == "test-model"
    assert response.provider == "fake"
