"""Mock ServiceNow tool for safe workflow execution."""

from typing import Any

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool


class MockServiceNowTool(BaseTool):
    name = "servicenow_tool"
    supported_actions = ("create_incident",)

    async def _execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        alert = inputs.get("alert", {})
        request_id = context.get("request_id")
        incident_number = f"INC-{request_id.upper()}" if request_id else "INC-MOCK"

        return ToolResult.ok(
            {
                "incident": {
                    "number": incident_number,
                    "alert_id": alert.get("id", "unknown"),
                    "severity": alert.get("severity", "unknown"),
                    "source": alert.get("source", "unknown"),
                    "status": "created",
                }
            }
        )
