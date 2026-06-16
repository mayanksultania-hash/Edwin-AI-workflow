"""Base contract for workflow tools."""

from abc import ABC, abstractmethod
from typing import Any

from ai_workflow.models.tool import ToolResult


class BaseTool(ABC):
    name: str
    supported_actions: tuple[str, ...]

    async def execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        if action not in self.supported_actions:
            return ToolResult.fail(
                f"Tool '{self.name}' does not support action '{action}'"
            )

        return await self._execute(action=action, inputs=inputs, context=context)

    @abstractmethod
    async def _execute(
        self,
        action: str,
        inputs: dict[str, Any],
        context: dict[str, Any],
    ) -> ToolResult:
        raise NotImplementedError
