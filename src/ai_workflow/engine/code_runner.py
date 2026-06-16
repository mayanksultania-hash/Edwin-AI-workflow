"""Run generated Python workflow code."""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from ai_workflow.models.execution import StepExecution, WorkflowExecution
from ai_workflow.tools.registry import ToolRegistry


async def run_generated_code(
    code_path: Path,
    registry: ToolRegistry,
    context: dict[str, Any],
) -> WorkflowExecution:
    module = _load_module(code_path)
    workflow_name = getattr(module, "WORKFLOW_NAME", code_path.stem)
    tools = {name: registry.get(name) for name in registry.names()}

    try:
        final_data = await module.main(context=context, tools=tools)
    except Exception as error:
        steps = _load_step_executions(module)
        return WorkflowExecution(
            workflow_name=workflow_name,
            success=False,
            steps=steps,
            error=str(error),
        )

    return WorkflowExecution(
        workflow_name=workflow_name,
        success=True,
        steps=_load_step_executions(module),
        final_data=final_data,
    )


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generated_workflow", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load generated code: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_step_executions(module: ModuleType) -> tuple[StepExecution, ...]:
    raw_steps = getattr(module, "LAST_STEP_EXECUTIONS", [])
    return tuple(
        StepExecution(
            step_id=raw_step["step_id"],
            tool=raw_step["tool"],
            action=raw_step["action"],
            success=raw_step["success"],
            data=raw_step.get("data", {}),
            error=raw_step.get("error"),
        )
        for raw_step in raw_steps
    )
