"""Access integration wrapper."""

from typing import Any

from ai_workflow.integrations.runtime import run_tool


async def request_access(**inputs: Any) -> Any:
    return await run_tool("access_tool", "request_access", dict(inputs))


async def grant_access(**inputs: Any) -> Any:
    return await run_tool("access_tool", "grant_access", dict(inputs))
