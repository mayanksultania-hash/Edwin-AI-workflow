from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.mock_alert_tool import MockAlertTool


def test_mock_alert_tool_creates_alert_from_event():
    result = asyncio.run(
        MockAlertTool().execute(
            action="create_or_update_alert",
            inputs={"event": {"severity": "critical", "source": "router"}},
            context={"request_id": "req-1"},
        )
    )

    assert result.success is True
    assert result.data["alert"]["id"] == "mock-alert-req-1"
    assert result.data["alert"]["severity"] == "critical"
    assert result.data["alert"]["source"] == "router"
    assert result.data["alert"]["status"] == "created_or_updated"


def test_mock_alert_tool_uses_defaults():
    result = asyncio.run(
        MockAlertTool().execute(
            action="create_or_update_alert",
            inputs={},
            context={},
        )
    )

    assert result.success is True
    assert result.data["alert"]["id"] == "mock-alert"
    assert result.data["alert"]["severity"] == "unknown"
    assert result.data["alert"]["source"] == "unknown"


def test_mock_alert_tool_rejects_unknown_action():
    result = asyncio.run(
        MockAlertTool().execute(
            action="delete_alert",
            inputs={},
            context={},
        )
    )

    assert result.success is False
    assert "does not support action" in result.error
