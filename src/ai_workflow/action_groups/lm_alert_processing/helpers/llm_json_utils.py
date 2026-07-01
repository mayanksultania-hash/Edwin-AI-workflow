"""Shared utilities for parsing LLM JSON responses."""

from typing import Any

from pydantic import TypeAdapter


def validate_llm_json(text: str, adapter: TypeAdapter, label: str) -> Any:
    try:
        return adapter.validate_json(clean_json_text(text))
    except ValueError as error:
        raise ValueError(f"Invalid LLM {label}: {error}") from error


def clean_json_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    return stripped
