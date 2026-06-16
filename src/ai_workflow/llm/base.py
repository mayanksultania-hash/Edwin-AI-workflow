"""Base contract for LLM providers."""

from abc import ABC, abstractmethod

from ai_workflow.models.llm import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError
