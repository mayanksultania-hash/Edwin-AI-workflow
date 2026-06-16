"""Mock access tool for safe workflow execution."""

from typing import Any

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool


class MockAccessTool(BaseTool):
    name = "access_tool"
    supported_actions = ("request_access", "grant_access")

    async def _execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        if action == "request_access":
            system = inputs.get("system") or inputs.get("resource") or "unknown"
            access_request = {
                "id": _request_id(context),
                "user": inputs.get("user", "unknown"),
                "system": system,
                "status": "requested",
            }
            return ToolResult.ok(
                {
                    "access_request": access_request,
                    "request": access_request,
                }
            )

        request = inputs.get("request", {})
        return ToolResult.ok(
            {
                "access_grant": {
                    "request_id": request.get("id", "unknown"),
                    "user": request.get("user", "unknown"),
                    "system": request.get("system", "unknown"),
                    "status": "granted",
                }
            }
        )


def _request_id(context: dict[str, Any]) -> str:
    request_id = context.get("request_id")
    return f"mock-access-{request_id}" if request_id else "mock-access"
