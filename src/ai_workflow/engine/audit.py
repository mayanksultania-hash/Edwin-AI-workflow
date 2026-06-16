"""Write audit records for workflow runs."""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ai_workflow.config.constants import DEFAULT_AUDIT_DIR
from ai_workflow.models.audit import AuditRecord
from ai_workflow.models.run import WorkflowRunResult


def build_audit_record(prompt: str, result: WorkflowRunResult) -> AuditRecord:
    return AuditRecord(
        run_id=str(uuid4()),
        prompt=prompt,
        workflow_name=result.workflow.name,
        workflow_yaml=result.workflow_yaml,
        generated_code=result.generated_code,
        execution_success=result.execution.success,
        final_data=result.execution.final_data,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def write_audit_record(
    record: AuditRecord,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
) -> Path:
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / f"{record.run_id}.json"
    audit_path.write_text(
        json.dumps(asdict(record), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return audit_path
