"""Write generated workflow files."""

from pathlib import Path

from ai_workflow.models.output import GeneratedOutputPaths
from ai_workflow.models.run import WorkflowRunResult


def write_generated_outputs(
    result: WorkflowRunResult,
    output_dir: Path,
    language: str,
) -> GeneratedOutputPaths:
    workflow_dir = output_dir / "workflows"
    code_dir = output_dir / "code"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    code_dir.mkdir(parents=True, exist_ok=True)

    workflow_yaml_path = workflow_dir / f"{result.workflow.name}.yaml"
    generated_code_path = code_dir / f"{result.workflow.name}{_code_extension(language)}"

    workflow_yaml_path.write_text(result.workflow_yaml, encoding="utf-8")
    generated_code_path.write_text(result.generated_code, encoding="utf-8")

    return GeneratedOutputPaths(
        workflow_yaml_path=workflow_yaml_path,
        generated_code_path=generated_code_path,
    )


def _code_extension(language: str) -> str:
    if language == "python":
        return ".py"

    if language == "typescript":
        return ".ts"

    raise ValueError(f"Unsupported output language: {language}")
