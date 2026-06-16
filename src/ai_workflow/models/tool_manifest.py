"""Data models for tool prompt metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolActionManifest:
    tool: str
    action: str

    @property
    def full_name(self) -> str:
        return f"{self.tool}.{self.action}"


@dataclass(frozen=True)
class ToolManifest:
    actions: tuple[ToolActionManifest, ...]

    def action_names(self) -> tuple[str, ...]:
        return tuple(action.full_name for action in self.actions)
