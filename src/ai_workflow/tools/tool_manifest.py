"""Build tool metadata for prompts and UI."""

from typing import Optional

from ai_workflow.models.tool_manifest import ToolActionManifest, ToolManifest
from ai_workflow.tools.default_registry import build_default_registry
from ai_workflow.tools.registry import ToolRegistry


def build_tool_manifest(registry: ToolRegistry) -> ToolManifest:
    actions: list[ToolActionManifest] = []

    for tool_name in registry.names():
        tool = registry.get(tool_name)
        for action in tool.supported_actions:
            actions.append(ToolActionManifest(tool=tool.name, action=action))

    return ToolManifest(actions=tuple(actions))


def build_default_tool_manifest(
    enabled_tools: Optional[tuple[str, ...]] = None,
) -> ToolManifest:
    registry = build_default_registry(enabled_tools=enabled_tools)
    return build_tool_manifest(registry)


def format_tool_manifest_for_prompt(manifest: ToolManifest) -> str:
    return "\n".join(f"- {action_name}" for action_name in manifest.action_names())
