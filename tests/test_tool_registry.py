from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool
from ai_workflow.tools.registry import ToolRegistry


class FirstTool(BaseTool):
    name = "first_tool"
    supported_actions = ("run",)

    async def _execute(self, action, inputs, context):
        return ToolResult.ok()


class SecondTool(BaseTool):
    name = "second_tool"
    supported_actions = ("run",)

    async def _execute(self, action, inputs, context):
        return ToolResult.ok()


def test_registry_registers_and_gets_tool():
    registry = ToolRegistry()
    tool = FirstTool()

    registry.register(tool)

    assert registry.get("first_tool") is tool


def test_registry_rejects_duplicate_tool_name():
    registry = ToolRegistry()
    registry.register(FirstTool())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(FirstTool())


def test_registry_rejects_missing_tool():
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="Tool not found"):
        registry.get("missing_tool")


def test_registry_lists_tool_names():
    registry = ToolRegistry()
    registry.register(FirstTool())
    registry.register(SecondTool())

    assert registry.names() == ("first_tool", "second_tool")


def test_registry_can_filter_enabled_tools():
    registry = ToolRegistry()
    registry.register(FirstTool())
    registry.register(SecondTool())

    filtered = registry.with_enabled_tools(("second_tool",))

    assert filtered.names() == ("second_tool",)
    assert filtered.get("second_tool").name == "second_tool"


def test_registry_rejects_unknown_enabled_tool():
    registry = ToolRegistry()
    registry.register(FirstTool())

    with pytest.raises(KeyError, match="Enabled tool not registered"):
        registry.with_enabled_tools(("missing_tool",))
