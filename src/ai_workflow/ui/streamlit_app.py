"""Streamlit app for the AI workflow runner."""

import asyncio
import json
from pathlib import Path
from typing import Any

from ai_workflow.app import run_action_group_workflow, run_ai_workflow
from ai_workflow.config.constants import PROJECT_ROOT
from ai_workflow.config.loader import load_config
from ai_workflow.action_groups.lm_alert_processing import (
    LMAlertProcessingCustomizer,
    build_lm_alert_processing_questions,
)
from ai_workflow.llm.provider_factory import build_llm_provider
from ai_workflow.models.action_group import ActionGroup
from ai_workflow.models.action_group_customization import ActionGroupCustomizationPlan
from ai_workflow.models.action_service import ActionServiceSubmitResult
from ai_workflow.models.execution import WorkflowExecution
from ai_workflow.models.orchestration import (
    CodeVerification,
    Intent,
    MCPContext,
    WorkflowPlan,
)
from ai_workflow.models.run import WorkflowRunResult
from ai_workflow.models.tool_manifest import ToolManifest
from ai_workflow.orchestration.context_requirements import MissingContextError
from ai_workflow.tools.tool_manifest import build_default_tool_manifest


DEFAULT_PROMPT = (
    "When a critical router event happens, create an alert and ServiceNow incident"
)

DEFAULT_ACTION_GROUP_PROMPT = (
    "Create an Incident Processing action group for ServiceNow incident updates"
)


def execution_steps_table(execution: WorkflowExecution) -> list[dict[str, Any]]:
    return [
        {
            "step_id": step.step_id,
            "tool": step.tool,
            "action": step.action,
            "success": step.success,
            "error": step.error or "",
        }
        for step in execution.steps
    ]


def tool_manifest_table(manifest: ToolManifest) -> list[dict[str, str]]:
    return [
        {
            "tool": action.tool,
            "action": action.action,
        }
        for action in manifest.actions
    ]


def intent_summary(intent: Intent | None) -> dict[str, Any]:
    if intent is None:
        return {}

    return {
        "name": intent.name,
        "domain": intent.domain,
        "summary": intent.summary,
        "entities": intent.entities,
    }


def mcp_context_summary(mcp_context: MCPContext | None) -> dict[str, Any]:
    if mcp_context is None:
        return {}

    return {
        "source": mcp_context.source,
        "values": mcp_context.values,
    }


def plan_steps_table(plan: WorkflowPlan | None) -> list[dict[str, Any]]:
    if plan is None:
        return []

    return [
        {
            "order": step.order,
            "goal": step.goal,
            "tool": step.tool,
            "action": step.action,
            "inputs": step.inputs,
        }
        for step in plan.steps
    ]


def action_group_general_summary(action_group: ActionGroup) -> dict[str, Any]:
    return {
        "name": action_group.name,
        "description": action_group.description,
        "source": action_group.source,
        "rule": action_group.rule,
        "steps": len(action_group.steps),
        "has_group_condition": action_group.group_condition is not None,
    }


def action_group_steps_table(action_group: ActionGroup) -> list[dict[str, Any]]:
    return [
        {
            "order": step.order,
            "action_type": step.action_type,
            "name": step.name,
            "start_condition": step.start_condition is not None,
            "stop_condition": step.stop_condition is not None,
            "mapped_fields": len(step.mapped_fields),
            "config": step.config,
        }
        for step in action_group.steps
    ]


def action_service_submit_summary(
    submit_result: ActionServiceSubmitResult | None,
) -> dict[str, Any]:
    if submit_result is None:
        return {
            "submitted": False,
            "message": "Preview only. Submit was not requested.",
        }

    return {
        "submitted": submit_result.submitted,
        "status_code": submit_result.status_code,
        "response_body": submit_result.response_body,
        "message": submit_result.message,
    }


def code_verification_summary(
    code_verification: CodeVerification | None,
) -> dict[str, Any]:
    if code_verification is None:
        return {}

    return {
        "approved": code_verification.approved,
        "risk_level": code_verification.risk_level,
        "summary": code_verification.summary,
        "issues": list(code_verification.issues),
    }


def customization_plan_summary(
    plan: ActionGroupCustomizationPlan,
) -> dict[str, Any]:
    return {
        "summary": plan.summary,
        "base_action_group_id": plan.base_action_group_id,
        "target_action_group_name": plan.target_action_group_name,
        "questions_used": plan.questions_used,
        "recommended_changes": plan.recommended_changes,
    }


def yaml_customization_summary(result: Any) -> dict[str, Any]:
    return {
        "patch_summary": result.patch_summary,
        "patches": result.patches,
        "output_path": str(result.output_path),
        "validation_passed": result.validation_passed,
        "validation_errors": result.validation_errors,
    }


def dry_run_summary(result: WorkflowRunResult) -> list[str]:
    lines = [
        f"Created workflow `{result.workflow.name}`.",
        f"Generated {len(result.workflow.steps)} workflow steps.",
        "Validated all tools and actions before execution.",
        "Executed mock tools only.",
    ]

    if result.execution.success:
        lines.append("Finished successfully.")
    else:
        lines.append(f"Stopped with error: {result.execution.error}")

    return lines


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title="AI Workflow Runner", layout="wide")
    st.title("AI Workflow Runner")

    with st.sidebar:
        st.header("Config")
        config_path = Path(
            st.text_input(
                "Config path",
                value=str(PROJECT_ROOT / "config" / "workflow_config.yaml"),
            )
        )
        version_path = Path(
            st.text_input("Version path", value=str(PROJECT_ROOT / "VERSION"))
        )
        audit_dir = Path(
            st.text_input("Audit directory", value=str(PROJECT_ROOT / "outputs" / "audit"))
        )
        output_dir = Path(
            st.text_input(
                "Generated output directory",
                value=str(PROJECT_ROOT / "outputs" / "generated"),
            )
        )

        st.header("Enabled Tools")
        try:
            config = load_config(config_path=config_path, version_path=version_path)
            manifest = build_default_tool_manifest(enabled_tools=config.enabled_tools)
            st.dataframe(tool_manifest_table(manifest), width="stretch")
        except Exception as error:
            st.warning(f"Could not load tools: {error}")

    mode = st.radio(
        "Builder mode",
        options=("Workflow code", "Action Group", "LM Alert guided setup"),
        horizontal=True,
    )
    default_prompt = (
        DEFAULT_ACTION_GROUP_PROMPT
        if mode in ("Action Group", "LM Alert guided setup")
        else DEFAULT_PROMPT
    )
    prompt = ""
    if mode != "LM Alert guided setup":
        prompt = st.text_area("Request", value=default_prompt, height=120)
    submit_action_group = False
    if mode == "Action Group":
        submit_action_group = st.checkbox(
            "Approve and submit Action Service JSON",
            value=False,
        )
    if mode == "LM Alert guided setup":
        st.write("Generate questions from the base YAML, answer them, then save final YAML.")
        st.caption(
            str(PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml")
        )
        if "lm_alert_questions" not in st.session_state:
            st.session_state["lm_alert_questions"] = []
        if st.button("Generate questions from base YAML"):
            config = load_config(config_path=config_path, version_path=version_path)
            if config.model_provider == "mock":
                st.error("LM Alert guided setup needs a real LLM provider, for example OpenAI.")
                return
            customizer = LMAlertProcessingCustomizer(
                llm_provider=build_llm_provider(config),
                model_name=config.model_name,
                max_output_tokens=config.model_max_output_tokens,
            )
            with st.spinner("Asking LLM to generate customization questions"):
                st.session_state["lm_alert_questions"] = list(
                    asyncio.run(customizer.generate_questions_from_base_yaml())
                )
        guided_answers: dict[str, str] = {}
        questions = st.session_state["lm_alert_questions"] or list(
            build_lm_alert_processing_questions()
        )
        for question in questions:
            guided_answers[question.key] = st.text_area(
                question.question,
                value=question.example_answer,
                height=80,
            )
    run_clicked = st.button(
        "Build customization plan"
        if mode == "LM Alert guided setup"
        else "Generate action group"
        if mode == "Action Group"
        else "Run workflow",
        type="primary",
    )

    if not run_clicked:
        return

    if mode != "LM Alert guided setup" and not prompt.strip():
        st.error("Enter a workflow request.")
        return

    if mode == "LM Alert guided setup":
        if any(not answer.strip() for answer in guided_answers.values()):
            st.error("Please answer all guided setup questions.")
            return

        with st.spinner("Building final LM Alert Processing YAML"):
            config = load_config(config_path=config_path, version_path=version_path)
            if config.model_provider == "mock":
                st.error("LM Alert guided setup needs a real LLM provider, for example OpenAI.")
                return
            customizer = LMAlertProcessingCustomizer(
                llm_provider=build_llm_provider(config),
                model_name=config.model_name,
                max_output_tokens=config.model_max_output_tokens,
            )
            try:
                result = asyncio.run(
                    customizer.customize_base_yaml(
                        answers={
                            key: value.strip()
                            for key, value in guided_answers.items()
                        },
                        output_dir=output_dir,
                        questions=tuple(questions),
                    )
                )
            except ValueError as error:
                st.error("Could not apply the LLM patch plan.")
                st.write(str(error))
                st.info("Restart Streamlit if this mentions a patch type that the current code supports.")
                return

        st.success("Final LM Alert Processing YAML generated")
        st.subheader("LM Alert Processing Guided Setup")
        setup_tabs = st.tabs(
            ["Patch Plan", "Final YAML", "Validation", "Files"]
        )
        with setup_tabs[0]:
            st.json(yaml_customization_summary(result))
        with setup_tabs[1]:
            st.code(result.final_yaml, language="yaml")
            st.download_button(
                "Download final YAML",
                data=result.final_yaml,
                file_name="lm_alert_processing_final.yaml",
                mime="text/yaml",
            )
        with setup_tabs[2]:
            if result.validation_passed:
                st.success("Final YAML passed structural validation.")
            else:
                st.error("Final YAML failed structural validation.")
                st.write("Errors:")
                for error in result.validation_errors:
                    st.write(f"- `{error}`")
        with setup_tabs[3]:
            st.json(
                {
                    "base_yaml_path": str(PROJECT_ROOT / "inputs" / "lm_alert_processing_base.yaml"),
                    "final_yaml_path": str(result.output_path),
                    "validation_passed": result.validation_passed,
                    "validation_error_count": len(result.validation_errors),
                }
            )
        return

    if mode == "Action Group":
        with st.spinner("Generating Action Group YAML and compiling Action Service JSON"):
            result = asyncio.run(
                run_action_group_workflow(
                    prompt=prompt.strip(),
                    config_path=config_path,
                    version_path=version_path,
                    output_dir=output_dir,
                    submit=submit_action_group,
                )
            )

        st.success(
            "Action Group submitted"
            if result.submit_result and result.submit_result.submitted
            else "Action Group generated and compiled"
        )
        st.subheader("Action Group Lifecycle")
        action_tabs = st.tabs(
            [
                "General",
                "Actions",
                "Action Group YAML",
                "Action Service JSON",
                "Submit Result",
                "Files",
            ]
        )
        with action_tabs[0]:
            st.json(action_group_general_summary(result.action_group))
        with action_tabs[1]:
            st.dataframe(action_group_steps_table(result.action_group), width="stretch")
        with action_tabs[2]:
            st.code(result.action_group_yaml, language="yaml")
        with action_tabs[3]:
            st.code(json.dumps(result.action_service_json, indent=2), language="json")
        with action_tabs[4]:
            st.json(action_service_submit_summary(result.submit_result))
        with action_tabs[5]:
            st.json(
                {
                    "action_group_yaml_path": (
                        str(result.action_group_output_paths.action_group_yaml_path)
                        if result.action_group_output_paths
                        else None
                    ),
                    "action_service_json_path": (
                        str(result.action_service_json_output_paths.action_service_json_path)
                        if result.action_service_json_output_paths
                        else None
                    ),
                }
            )
        return

    with st.spinner("Detecting intent, planning, generating code, and running workflow"):
        try:
            result = asyncio.run(
                run_ai_workflow(
                    prompt=prompt.strip(),
                    config_path=config_path,
                    version_path=version_path,
                    audit_dir=audit_dir,
                    output_dir=output_dir,
                )
            )
        except MissingContextError as error:
            st.error("More information is needed before this workflow can be created.")
            st.write("Missing values:")
            for key in error.missing_keys:
                st.write(f"- `{key}`")
            st.write("Questions:")
            for question in error.questions:
                st.write(f"- {question}")
            return

    st.success("Workflow completed" if result.execution.success else "Workflow failed")

    st.subheader("Workflow Lifecycle")
    lifecycle_tabs = st.tabs(
        [
            "Intent",
            "MCP Context",
            "Plan",
            "Workflow YAML",
            "Generated Code",
            "Code Verification",
            "Execution",
            "Final Output",
            "Dry Run Summary",
        ]
    )
    with lifecycle_tabs[0]:
        st.json(intent_summary(result.intent))
    with lifecycle_tabs[1]:
        st.json(mcp_context_summary(result.mcp_context))
    with lifecycle_tabs[2]:
        st.dataframe(plan_steps_table(result.plan), width="stretch")
    with lifecycle_tabs[3]:
        st.code(result.workflow_yaml, language="yaml")
    with lifecycle_tabs[4]:
        st.code(result.generated_code)
    with lifecycle_tabs[5]:
        st.json(code_verification_summary(result.code_verification))
    with lifecycle_tabs[6]:
        st.dataframe(execution_steps_table(result.execution), width="stretch")
    with lifecycle_tabs[7]:
        st.json(result.execution.final_data)
    with lifecycle_tabs[8]:
        for line in dry_run_summary(result):
            st.write(f"- {line}")


def main() -> None:
    """Launch the Streamlit demo app."""
    import sys

    from streamlit.web import cli as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        str(Path(__file__).resolve()),
    ]
    raise SystemExit(streamlit_cli.main())


if __name__ == "__main__":
    run_streamlit_app()
