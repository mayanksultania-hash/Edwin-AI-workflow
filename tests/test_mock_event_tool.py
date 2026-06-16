from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.mock_event_tool import MockEventTool


def test_mock_event_tool_matches_event():
    result = asyncio.run(
        MockEventTool().execute(
            action="match_event",
            inputs={"severity": "critical", "source": "router"},
            context={"request_id": "req-1"},
        )
    )

    assert result.success is True
    assert result.data["matched"] is True
    assert result.data["event"]["severity"] == "critical"
    assert result.data["event"]["source"] == "router"
    assert result.data["event"]["request_id"] == "req-1"


def test_mock_event_tool_uses_defaults():
    result = asyncio.run(
        MockEventTool().execute(
            action="match_event",
            inputs={},
            context={},
        )
    )

    assert result.success is True
    assert result.data["event"]["severity"] == "unknown"
    assert result.data["event"]["source"] == "unknown"


def test_mock_event_tool_rejects_unknown_action():
    result = asyncio.run(
        MockEventTool().execute(
            action="create_event",
            inputs={},
            context={},
        )
    )

    assert result.success is False
    assert "does not support action" in result.error
