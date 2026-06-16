from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.default_registry import build_default_registry


def test_default_registry_contains_mock_tools():
    registry = build_default_registry()

    assert registry.names() == (
        "event_tool",
        "alert_tool",
        "servicenow_tool",
        "access_tool",
    )


def test_default_registry_can_filter_enabled_tools():
    registry = build_default_registry(enabled_tools=("access_tool",))

    assert registry.names() == ("access_tool",)
    assert registry.get("access_tool").name == "access_tool"
