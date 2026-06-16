"""OpenAI LLM provider."""

from pathlib import Path
from typing import Any, Optional

from ai_workflow.config.constants import DEFAULT_ENV_PATH
from ai_workflow.config.env import get_env_value
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMRequest, LLMResponse


class OpenAILLMProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key_env_var: str,
        env_path: Path = DEFAULT_ENV_PATH,
        client: Optional[Any] = None,
    ) -> None:
        self.api_key_env_var = api_key_env_var
        self.env_path = env_path
        self.client = client

    async def generate(self, request: LLMRequest) -> LLMResponse:
        client = self.client or self._build_client()
        create_args = {
            "model": request.model_name,
            "input": request.prompt,
        }
        if request.max_output_tokens:
            create_args["max_output_tokens"] = request.max_output_tokens

        response = await client.responses.create(**create_args)

        return LLMResponse(
            text=_extract_text(response),
            model_name=request.model_name,
            provider=self.provider_name,
            raw_response=_to_raw_response(response),
        )

    def _build_client(self) -> Any:
        api_key = get_env_value(self.api_key_env_var, self.env_path)
        if not api_key:
            raise ValueError(f"Missing API key env value: {self.api_key_env_var}")

        try:
            from openai import AsyncOpenAI
        except ModuleNotFoundError as error:
            raise RuntimeError("OpenAI SDK is not installed") from error

        return AsyncOpenAI(api_key=api_key)


def _extract_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    if isinstance(response, dict):
        return response.get("output_text", "")

    return ""


def _to_raw_response(response: Any) -> Optional[dict]:
    if isinstance(response, dict):
        return response

    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        return model_dump()

    return None
