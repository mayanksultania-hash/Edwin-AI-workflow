"""Tool models used by workflow tools."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ToolResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Optional[dict[str, Any]] = None) -> "ToolResult":
        return cls(success=True, data=data or {})

    @classmethod
    def fail(cls, error: str, data: Optional[dict[str, Any]] = None) -> "ToolResult":
        return cls(success=False, data=data or {}, error=error)
