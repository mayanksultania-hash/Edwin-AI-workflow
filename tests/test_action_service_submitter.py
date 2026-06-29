from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.mcp.action_service_submitter import (
    DisabledActionServiceSubmitter,
    HttpActionServiceSubmitter,
)


def test_disabled_action_service_submitter_returns_preview_only_result():
    result = DisabledActionServiceSubmitter().submit_action_group({"name": "Test"})

    assert result.submitted is False
    assert result.message == "Action Service submit is disabled"


def test_http_action_service_submitter_posts_compiled_json():
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append((url, headers, payload, timeout_seconds))
        return {
            "submitted": True,
            "status_code": 201,
            "body": {"actionGroupId": "created-id"},
            "message": "created",
        }

    submitter = HttpActionServiceSubmitter(
        base_url="http://action:8447/",
        endpoint_path="/action/group",
        headers={"Authorization": "Bearer token"},
        timeout_seconds=2.5,
        http_post_json=fake_post_json,
    )

    result = submitter.submit_action_group({"name": "Create Incident"})

    assert calls == [
        (
            "http://action:8447/action/group",
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer token",
            },
            {"name": "Create Incident"},
            2.5,
        )
    ]
    assert result.submitted is True
    assert result.status_code == 201
    assert result.response_body == {"actionGroupId": "created-id"}
    assert result.message == "created"
