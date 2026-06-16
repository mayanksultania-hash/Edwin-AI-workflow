"""Event integration wrapper."""

from typing import Any

from ai_workflow.integrations.runtime import run_tool


async def match_event(**inputs: Any) -> Any:
    return await run_tool("event_tool", "match_event", dict(inputs))
