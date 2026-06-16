"""Registry for workflow tools."""

from ai_workflow.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError as error:
            raise KeyError(f"Tool not found: {name}") from error

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def with_enabled_tools(self, enabled_tools: tuple[str, ...]) -> "ToolRegistry":
        filtered = ToolRegistry()

        for tool_name in enabled_tools:
            if tool_name not in self._tools:
                raise KeyError(f"Enabled tool not registered: {tool_name}")
            filtered.register(self._tools[tool_name])

        return filtered
