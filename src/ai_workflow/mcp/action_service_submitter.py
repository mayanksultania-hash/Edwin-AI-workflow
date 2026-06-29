"""Submit compiled Action Groups to Action Service."""

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_workflow.models.action_service import ActionServiceSubmitResult


class ActionServiceSubmitter(Protocol):
    """Submits compiled Action Service JSON."""

    def submit_action_group(self, action_service_json: dict[str, Any]) -> ActionServiceSubmitResult:
        """Submit compiled Action Service JSON."""


class ActionServiceSubmitError(RuntimeError):
    """Raised when Action Service submit fails before a response is available."""


@dataclass(frozen=True)
class DisabledActionServiceSubmitter:
    """Submitter used when real writes are disabled."""

    def submit_action_group(self, action_service_json: dict[str, Any]) -> ActionServiceSubmitResult:
        return ActionServiceSubmitResult(
            submitted=False,
            message="Action Service submit is disabled",
        )


@dataclass(frozen=True)
class HttpActionServiceSubmitter:
    """Submits Action Groups to an Action Service HTTP endpoint."""

    base_url: str
    endpoint_path: str = "/action/group"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 10.0
    http_post_json: Callable[[str, dict[str, str], dict[str, Any], float], Any] | None = None

    def submit_action_group(self, action_service_json: dict[str, Any]) -> ActionServiceSubmitResult:
        url = self._submit_url()
        if self.http_post_json:
            response = self.http_post_json(
                url,
                self._headers(),
                action_service_json,
                self.timeout_seconds,
            )
            return _result_from_response(response)

        return _default_http_post_json(
            url=url,
            headers=self._headers(),
            payload=action_service_json,
            timeout_seconds=self.timeout_seconds,
        )

    def _submit_url(self) -> str:
        base_url = self.base_url.rstrip("/")
        endpoint = self.endpoint_path if self.endpoint_path.startswith("/") else f"/{self.endpoint_path}"
        return f"{base_url}{endpoint}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update(self.headers)
        return headers


def _default_http_post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> ActionServiceSubmitResult:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
            status_code = response.getcode()
    except HTTPError as error:
        raw_body = error.read().decode("utf-8")
        return ActionServiceSubmitResult(
            submitted=False,
            status_code=error.code,
            response_body=_parse_response_body(raw_body),
            message=f"Action Service submit failed with HTTP {error.code}",
        )
    except URLError as error:
        raise ActionServiceSubmitError(f"Action Service submit failed: {url}") from error

    return ActionServiceSubmitResult(
        submitted=True,
        status_code=status_code,
        response_body=_parse_response_body(raw_body),
        message="Action Service submit completed",
    )


def _result_from_response(response: Any) -> ActionServiceSubmitResult:
    if isinstance(response, ActionServiceSubmitResult):
        return response

    if isinstance(response, dict):
        status_code = response.get("status_code") or response.get("statusCode")
        submitted = response.get("submitted", True)
        return ActionServiceSubmitResult(
            submitted=bool(submitted),
            status_code=status_code if isinstance(status_code, int) else None,
            response_body=response.get("body", response),
            message=str(response.get("message", "Action Service submit completed")),
        )

    return ActionServiceSubmitResult(
        submitted=True,
        response_body=response,
        message="Action Service submit completed",
    )


def _parse_response_body(raw_body: str) -> Any:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body
