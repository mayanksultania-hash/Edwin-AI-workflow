from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.mock_access_tool import MockAccessTool


def test_mock_access_tool_requests_access():
    result = asyncio.run(
        MockAccessTool().execute(
            action="request_access",
            inputs={"user": "John", "system": "Tableau"},
            context={"request_id": "req-1"},
        )
    )

    assert result.success is True
    assert result.data["access_request"]["id"] == "mock-access-req-1"
    assert result.data["access_request"]["user"] == "John"
    assert result.data["access_request"]["system"] == "Tableau"
    assert result.data["access_request"]["status"] == "requested"
    assert result.data["request"] == result.data["access_request"]


def test_mock_access_tool_accepts_resource_alias():
    result = asyncio.run(
        MockAccessTool().execute(
            action="request_access",
            inputs={"user": "John", "resource": "Tableau"},
            context={},
        )
    )

    assert result.success is True
    assert result.data["access_request"]["system"] == "Tableau"


def test_mock_access_tool_grants_access():
    result = asyncio.run(
        MockAccessTool().execute(
            action="grant_access",
            inputs={
                "request": {
                    "id": "mock-access-req-1",
                    "user": "John",
                    "system": "Tableau",
                }
            },
            context={},
        )
    )

    assert result.success is True
    assert result.data["access_grant"]["request_id"] == "mock-access-req-1"
    assert result.data["access_grant"]["user"] == "John"
    assert result.data["access_grant"]["system"] == "Tableau"
    assert result.data["access_grant"]["status"] == "granted"


def test_mock_access_tool_rejects_unknown_action():
    result = asyncio.run(
        MockAccessTool().execute(
            action="remove_access",
            inputs={},
            context={},
        )
    )

    assert result.success is False
    assert "does not support action" in result.error
