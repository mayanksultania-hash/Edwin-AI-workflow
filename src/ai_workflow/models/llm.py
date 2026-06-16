"""LLM models for provider calls."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    model_name: str
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model_name: str
    provider: str
    raw_response: Optional[dict] = None
