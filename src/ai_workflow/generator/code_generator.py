"""Generate simple workflow code from a workflow model."""

from ai_workflow.config.constants import SUPPORTED_LANGUAGES
from ai_workflow.generator.code_templates import (
    render_python_workflow,
    render_typescript_workflow,
)
from ai_workflow.models.workflow import Workflow


def generate_workflow_code(workflow: Workflow, language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported code language: {language}")

    if language == "python":
        return render_python_workflow(workflow)

    if language == "typescript":
        return render_typescript_workflow(workflow)

    raise ValueError(f"Code generator is not implemented for: {language}")
