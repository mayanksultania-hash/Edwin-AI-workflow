"""Action Service submit models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionServiceSubmitResult:
    submitted: bool
    status_code: int | None = None
    response_body: Any = None
    message: str = ""
