"""ServiceNow integration wrapper."""

from typing import Any

from ai_workflow.integrations.runtime import run_tool


async def create_incident(**inputs: Any) -> Any:
    return await run_tool("servicenow_tool", "create_incident", dict(inputs))
