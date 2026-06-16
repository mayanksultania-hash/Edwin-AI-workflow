from pathlib import Path
import sys
import asyncio


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.models.tool import ToolResult
from ai_workflow.tools.base import BaseTool


class SampleTool(BaseTool):
    name = "sample_tool"
    supported_actions = ("echo",)

    async def _execute(self, action, inputs, context):
        return ToolResult.ok(
            {
                "action": action,
                "inputs": inputs,
                "context": context,
            }
        )


def test_tool_result_ok():
    result = ToolResult.ok({"id": "123"})

    assert result.success is True
    assert result.data == {"id": "123"}
    assert result.error is None


def test_tool_result_fail():
    result = ToolResult.fail("something failed")

    assert result.success is False
    assert result.data == {}
    assert result.error == "something failed"


def test_base_tool_executes_supported_action():
    result = asyncio.run(
        SampleTool().execute(
            action="echo",
            inputs={"message": "hello"},
            context={"request_id": "req-1"},
        )
    )

    assert result.success is True
    assert result.data["action"] == "echo"
    assert result.data["inputs"] == {"message": "hello"}
    assert result.data["context"] == {"request_id": "req-1"}


def test_base_tool_rejects_unsupported_action():
    result = asyncio.run(
        SampleTool().execute(
            action="missing",
            inputs={},
            context={},
        )
    )

    assert result.success is False
    assert result.error == "Tool 'sample_tool' does not support action 'missing'"
