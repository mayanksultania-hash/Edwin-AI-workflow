"""Mock event tool for safe workflow execution."""

from typing import Any

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool


class MockEventTool(BaseTool):
    name = "event_tool"
    supported_actions = ("match_event",)

    async def _execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        event = {
            "severity": inputs.get("severity", "unknown"),
            "source": inputs.get("source", "unknown"),
            "request_id": context.get("request_id"),
        }

        return ToolResult.ok(
            {
                "matched": True,
                "event": event,
            }
        )
