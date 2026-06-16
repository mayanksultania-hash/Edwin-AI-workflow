"""Mock alert tool for safe workflow execution."""

from typing import Any

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool


class MockAlertTool(BaseTool):
    name = "alert_tool"
    supported_actions = ("create_or_update_alert",)

    async def _execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        event = inputs.get("event", {})
        request_id = context.get("request_id")
        alert_id = f"mock-alert-{request_id}" if request_id else "mock-alert"

        return ToolResult.ok(
            {
                "alert": {
                    "id": alert_id,
                    "severity": event.get("severity", "unknown"),
                    "source": event.get("source", "unknown"),
                    "status": "created_or_updated",
                }
            }
        )
