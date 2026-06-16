from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.tools.default_registry import build_default_registry
from ai_workflow.tools.tool_manifest import (
    build_default_tool_manifest,
    build_tool_manifest,
    format_tool_manifest_for_prompt,
)


def test_tool_manifest_lists_registered_tool_actions():
    registry = build_default_registry(enabled_tools=("access_tool",))

    manifest = build_tool_manifest(registry)

    assert manifest.action_names() == (
        "access_tool.request_access",
        "access_tool.grant_access",
    )


def test_default_tool_manifest_uses_enabled_tools():
    manifest = build_default_tool_manifest(enabled_tools=("servicenow_tool",))

    assert manifest.action_names() == ("servicenow_tool.create_incident",)


def test_tool_manifest_formats_prompt_lines():
    manifest = build_default_tool_manifest(enabled_tools=("event_tool",))

    assert format_tool_manifest_for_prompt(manifest) == "- event_tool.match_event"
