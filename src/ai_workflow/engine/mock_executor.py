"""Execute workflows with mock tools."""

from typing import Any

from ai_workflow.engine.input_resolver import resolve_step_inputs
from ai_workflow.models.execution import StepExecution, WorkflowExecution
from ai_workflow.models.workflow import Workflow
from ai_workflow.tools.registry import ToolRegistry


async def execute_mock_workflow(
    workflow: Workflow,
    registry: ToolRegistry,
    context: dict[str, Any],
) -> WorkflowExecution:
    step_results: list[StepExecution] = []
    previous_data: dict[str, Any] = {}
    step_outputs: dict[str, dict[str, Any]] = {}

    for step in workflow.steps:
        tool = registry.get(step.tool)
        inputs = resolve_step_inputs(
            step=step,
            previous_data=previous_data,
            step_outputs=step_outputs,
            context=context,
        )
        result = await tool.execute(
            action=step.action,
            inputs=inputs,
            context=context,
        )

        step_execution = StepExecution(
            step_id=step.id,
            tool=step.tool,
            action=step.action,
            success=result.success,
            data=result.data,
            error=result.error,
        )
        step_results.append(step_execution)

        if not result.success:
            return WorkflowExecution(
                workflow_name=workflow.name,
                success=False,
                steps=tuple(step_results),
                final_data=result.data,
                error=result.error,
            )

        previous_data = result.data
        step_outputs[step.id] = result.data

    return WorkflowExecution(
        workflow_name=workflow.name,
        success=True,
        steps=tuple(step_results),
        final_data=previous_data,
    )
