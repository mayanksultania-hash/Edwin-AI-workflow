"""Runtime binding for generated workflow integration calls."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any


_TOOLS: ContextVar[dict[str, Any] | None] = ContextVar("workflow_tools", default=None)
_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar("workflow_context", default=None)


@contextmanager
def bind_runtime(tools: dict[str, Any], context: dict[str, Any]) -> Iterator[None]:
    tools_token = _TOOLS.set(tools)
    context_token = _CONTEXT.set(context)
    try:
        yield
    finally:
        _CONTEXT.reset(context_token)
        _TOOLS.reset(tools_token)


async def run_tool(tool: str, action: str, inputs: dict[str, Any]) -> Any:
    tools = _TOOLS.get()
    context = _CONTEXT.get()
    if tools is None or context is None:
        raise RuntimeError("Workflow integrations are not bound to a runtime")

    return await tools[tool].execute(
        action=action,
        inputs=inputs,
        context=context,
    )
