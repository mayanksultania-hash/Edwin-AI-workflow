"""Alert integration wrapper."""

from typing import Any

from ai_workflow.integrations.runtime import run_tool


async def create_or_update_alert(**inputs: Any) -> Any:
    return await run_tool("alert_tool", "create_or_update_alert", dict(inputs))
