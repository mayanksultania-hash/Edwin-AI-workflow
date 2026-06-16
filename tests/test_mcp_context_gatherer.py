from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.mcp.context_gatherer import MockMCPContextGatherer
from ai_workflow.models.orchestration import Intent
from ai_workflow.tools.tool_manifest import build_default_tool_manifest


def test_mock_mcp_context_gatherer_returns_available_actions():
    intent = Intent(
        name="access_request",
        domain="identity_access",
        summary="Create an access workflow",
        entities={"user": "John", "system": "Tableau"},
    )
    manifest = build_default_tool_manifest(enabled_tools=("access_tool",))

    context = asyncio.run(
        MockMCPContextGatherer().gather(
            user_request="Give John Tableau access",
            intent=intent,
            tool_manifest=manifest,
        )
    )

    assert context.source == "mock_mcp"
    assert context.values["intent"] == "access_request"
    assert context.values["available_actions"] == [
        "access_tool.request_access",
        "access_tool.grant_access",
    ]
    assert context.values["schema_hints"]["access_tool.request_access"] == [
        "user",
        "system",
    ]
    assert context.values["context_keys"] == ["user", "system"]
