"""MCP-style context gathering for workflow generation."""

from ai_workflow.models.orchestration import Intent, MCPContext
from ai_workflow.models.tool_manifest import ToolManifest


class MockMCPContextGatherer:
    source = "mock_mcp"

    async def gather(
        self,
        user_request: str,
        intent: Intent,
        tool_manifest: ToolManifest,
    ) -> MCPContext:
        return MCPContext(
            source=self.source,
            values={
                "user_request": user_request,
                "intent": intent.name,
                "domain": intent.domain,
                "available_actions": list(tool_manifest.action_names()),
                "schema_hints": _schema_hints(intent, tool_manifest),
                "context_keys": _context_keys(intent),
            },
        )


def _schema_hints(intent: Intent, tool_manifest: ToolManifest) -> dict[str, list[str]]:
    available_actions = set(tool_manifest.action_names())
    if intent.name == "access_request":
        return _enabled_hints({
            "access_tool.request_access": ["user", "system"],
            "access_tool.grant_access": ["request"],
        }, available_actions)

    if intent.name in {"incident_workflow", "general_workflow"}:
        return _enabled_hints({
            "event_tool.match_event": ["event_type", "severity", "source"],
            "alert_tool.create_or_update_alert": ["event"],
            "servicenow_tool.create_incident": ["event", "alert"],
        }, available_actions)

    return {}


def _enabled_hints(
    hints: dict[str, list[str]],
    available_actions: set[str],
) -> dict[str, list[str]]:
    return {
        action_name: inputs
        for action_name, inputs in hints.items()
        if action_name in available_actions
    }


def _context_keys(intent: Intent) -> list[str]:
    if intent.name == "access_request":
        return ["user", "system"]

    return []
