from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.mock_servicenow_tool import MockServiceNowTool


def test_mock_servicenow_tool_creates_incident_from_alert():
    result = asyncio.run(
        MockServiceNowTool().execute(
            action="create_incident",
            inputs={
                "alert": {
                    "id": "mock-alert-req-1",
                    "severity": "critical",
                    "source": "router",
                }
            },
            context={"request_id": "req-1"},
        )
    )

    assert result.success is True
    assert result.data["incident"]["number"] == "INC-REQ-1"
    assert result.data["incident"]["alert_id"] == "mock-alert-req-1"
    assert result.data["incident"]["severity"] == "critical"
    assert result.data["incident"]["source"] == "router"
    assert result.data["incident"]["status"] == "created"


def test_mock_servicenow_tool_uses_defaults():
    result = asyncio.run(
        MockServiceNowTool().execute(
            action="create_incident",
            inputs={},
            context={},
        )
    )

    assert result.success is True
    assert result.data["incident"]["number"] == "INC-MOCK"
    assert result.data["incident"]["alert_id"] == "unknown"
    assert result.data["incident"]["severity"] == "unknown"
    assert result.data["incident"]["source"] == "unknown"


def test_mock_servicenow_tool_rejects_unknown_action():
    result = asyncio.run(
        MockServiceNowTool().execute(
            action="close_incident",
            inputs={},
            context={},
        )
    )

    assert result.success is False
    assert "does not support action" in result.error
