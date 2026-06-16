"""Build the default tool registry."""

from typing import Optional

from ai_workflow.tools.mock_access_tool import MockAccessTool
from ai_workflow.tools.mock_alert_tool import MockAlertTool
from ai_workflow.tools.mock_event_tool import MockEventTool
from ai_workflow.tools.mock_servicenow_tool import MockServiceNowTool
from ai_workflow.tools.registry import ToolRegistry


def build_default_registry(
    enabled_tools: Optional[tuple[str, ...]] = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(MockEventTool())
    registry.register(MockAlertTool())
    registry.register(MockServiceNowTool())
    registry.register(MockAccessTool())

    if enabled_tools:
        return registry.with_enabled_tools(enabled_tools)

    return registry
