"""Write detailed checkpoint files for workflow test runs."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_workflow.models.run import WorkflowRunResult


def write_run_checkpoint(
    prompt: str,
    result: WorkflowRunResult,
    checkpoint_dir: Path,
) -> Path:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid4())
    path = checkpoint_dir / f"{run_id}.json"
    path.write_text(
        json.dumps(
            build_run_checkpoint(prompt=prompt, result=result, run_id=run_id),
            indent=2,
            sort_keys=True,
            default=_json_default,
        ),
        encoding="utf-8",
    )
    return path


def build_run_checkpoint(
    prompt: str,
    result: WorkflowRunResult,
    run_id: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "checkpoints": {
            "intent": _to_json(result.intent),
            "mcp_context": _to_json(result.mcp_context),
            "plan": _to_json(result.plan),
            "workflow_yaml": result.workflow_yaml,
            "generated_code": result.generated_code,
            "code_verification": _to_json(result.code_verification),
            "execution": _to_json(result.execution),
            "files": {
                "audit_path": result.audit_path,
                "workflow_yaml_path": (
                    result.output_paths.workflow_yaml_path
                    if result.output_paths
                    else None
                ),
                "generated_code_path": (
                    result.output_paths.generated_code_path
                    if result.output_paths
                    else None
                ),
            },
        },
    }


def _to_json(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    return value


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)
