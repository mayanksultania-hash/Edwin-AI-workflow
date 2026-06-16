from pathlib import Path
import asyncio
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.config.models import WorkflowConfig
from ai_workflow.engine.validator import WorkflowToolValidationError
from ai_workflow.engine.workflow_runner import run_workflow_pipeline
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.models.llm import LLMResponse
from ai_workflow.orchestration.context_requirements import MissingContextError
from ai_workflow.tools.default_registry import build_default_registry


def sample_config(output_language="python"):
    return WorkflowConfig(
        model_provider="mock",
        model_name="mock-workflow-model",
        model_api_key_env_var="OPENAI_API_KEY",
        model_max_output_tokens=800,
        output_language=output_language,
        workflow_version="v0.1",
        execution_mode="mock",
        enabled_tools=("event_tool", "alert_tool", "servicenow_tool"),
    )


def test_run_workflow_pipeline_returns_full_result(tmp_path):
    result = asyncio.run(
        run_workflow_pipeline(
            prompt="Create workflow",
            config=sample_config(),
            llm_provider=MockLLMProvider(),
            registry=build_default_registry(),
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert result.workflow.name == "critical_router_event_workflow"
    assert result.intent.name == "general_workflow"
    assert result.mcp_context.source == "mock_mcp"
    assert result.plan.steps
    assert result.execution.success is True
    assert result.audit_path is not None
    assert result.audit_path.exists()
    assert result.output_paths is not None
    assert result.output_paths.workflow_yaml_path.exists()
    assert result.output_paths.generated_code_path.exists()


def test_run_workflow_pipeline_uses_configured_language(tmp_path):
    result = asyncio.run(
        run_workflow_pipeline(
            prompt="Create workflow",
            config=sample_config(output_language="typescript"),
            llm_provider=MockLLMProvider(),
            registry=build_default_registry(),
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert "export async function main(" in result.generated_code
    assert result.output_paths.generated_code_path.suffix == ".ts"


class UnknownToolProvider(BaseLLMProvider):
    provider_name = "unknown_tool"

    async def generate(self, request):
        if "Intent detection task." in request.prompt:
            return LLMResponse(
                text="""{
  "name": "general_workflow",
  "domain": "automation",
  "summary": "Create workflow",
  "entities": {}
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        if "Plan creation task." in request.prompt:
            return LLMResponse(
                text="""{
  "steps": [
    {
      "order": 1,
      "goal": "Check event",
      "tool": "event_tool",
      "action": "match_event",
      "inputs": {}
    }
  ]
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        return LLMResponse(
            text="""workflow:
  name: bad_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: bad
  steps:
    - id: bad_step
      tool: missing_tool
      action: run
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_run_workflow_pipeline_validates_tools_before_execution(tmp_path):
    with pytest.raises(WorkflowToolValidationError, match="unknown tool"):
        asyncio.run(
            run_workflow_pipeline(
                prompt="Create bad workflow",
                config=sample_config(),
                llm_provider=UnknownToolProvider(),
                registry=build_default_registry(),
                audit_dir=tmp_path / "audit",
                output_dir=tmp_path / "generated",
            )
        )


class PromptCapturingProvider(BaseLLMProvider):
    provider_name = "prompt_capture"

    def __init__(self):
        self.prompts = []
        self.last_prompt = None
        self.last_workflow_prompt = None
        self.last_max_output_tokens = None

    async def generate(self, request):
        self.prompts.append(request.prompt)
        self.last_prompt = request.prompt
        self.last_max_output_tokens = request.max_output_tokens

        if "Intent detection task." in request.prompt:
            return LLMResponse(
                text="""{
  "name": "general_workflow",
  "domain": "automation",
  "summary": "Create event workflow",
  "entities": {}
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        if "Plan creation task." in request.prompt:
            return LLMResponse(
                text="""{
  "steps": [
    {
      "order": 1,
      "goal": "Check event",
      "tool": "event_tool",
      "action": "match_event",
      "inputs": {}
    }
  ]
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        if "Generated code verification task." in request.prompt:
            return LLMResponse(
                text="""{
  "approved": true,
  "risk_level": "low",
  "summary": "Generated code is aligned.",
  "issues": []
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        self.last_workflow_prompt = request.prompt
        return LLMResponse(
            text="""workflow:
  name: event_only_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: event only
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_run_workflow_pipeline_uses_registry_tools_in_generation_prompt(tmp_path):
    provider = PromptCapturingProvider()

    asyncio.run(
        run_workflow_pipeline(
            prompt="Create event workflow",
            config=sample_config(),
            llm_provider=provider,
            registry=build_default_registry(enabled_tools=("event_tool",)),
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert "event_tool.match_event" in provider.last_workflow_prompt
    assert "servicenow_tool.create_incident" not in provider.last_workflow_prompt
    assert "Detected intent:" in provider.last_workflow_prompt
    assert "MCP context:" in provider.last_workflow_prompt
    assert "Plan:" in provider.last_workflow_prompt


def test_run_workflow_pipeline_sends_configured_max_output_tokens(tmp_path):
    provider = PromptCapturingProvider()

    asyncio.run(
        run_workflow_pipeline(
            prompt="Create event workflow",
            config=sample_config(),
            llm_provider=provider,
            registry=build_default_registry(enabled_tools=("event_tool",)),
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert provider.last_max_output_tokens == 800


class RejectingVerifierProvider(PromptCapturingProvider):
    provider_name = "rejecting_verifier"

    async def generate(self, request):
        if "Generated code verification task." in request.prompt:
            return LLMResponse(
                text="""{
  "approved": false,
  "risk_level": "high",
  "summary": "Generated code is missing an expected step.",
  "issues": ["missing step"]
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        return await super().generate(request)


def test_run_workflow_pipeline_stops_when_code_verifier_rejects(tmp_path):
    result = asyncio.run(
        run_workflow_pipeline(
            prompt="Create event workflow",
            config=sample_config(),
            llm_provider=RejectingVerifierProvider(),
            registry=build_default_registry(enabled_tools=("event_tool",)),
            audit_dir=tmp_path / "audit",
            output_dir=tmp_path / "generated",
        )
    )

    assert result.code_verification.approved is False
    assert result.execution.success is False
    assert "LLM code verification failed" in result.execution.error
    assert result.execution.steps == ()
    assert result.output_paths.generated_code_path.exists()
    assert result.audit_path.exists()


class MissingUserProvider(BaseLLMProvider):
    provider_name = "missing_user"

    def __init__(self):
        self.prompts = []

    async def generate(self, request):
        self.prompts.append(request.prompt)

        if "Intent detection task." in request.prompt:
            return LLMResponse(
                text="""{
  "name": "access_request",
  "domain": "access_management",
  "summary": "Create access workflow",
  "entities": {"system": "Tableau"}
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        if "Plan creation task." in request.prompt:
            return LLMResponse(
                text="""{
  "steps": [
    {
      "order": 1,
      "goal": "Request access",
      "tool": "access_tool",
      "action": "request_access",
      "inputs": {"system": "Tableau"}
    }
  ]
}""",
                model_name=request.model_name,
                provider=self.provider_name,
            )

        return LLMResponse(
            text="""workflow:
  name: access_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: access
  steps:
    - id: request_access
      tool: access_tool
      action: request_access
      inputs:
        system: Tableau
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_run_workflow_pipeline_raises_when_required_context_is_missing(tmp_path):
    provider = MissingUserProvider()
    config = WorkflowConfig(
        model_provider="mock",
        model_name="mock-workflow-model",
        model_api_key_env_var="OPENAI_API_KEY",
        model_max_output_tokens=800,
        output_language="python",
        workflow_version="v0.1",
        execution_mode="mock",
        enabled_tools=("access_tool",),
    )

    with pytest.raises(MissingContextError) as error:
        asyncio.run(
            run_workflow_pipeline(
                prompt="Give Tableau access",
                config=config,
                llm_provider=provider,
                registry=build_default_registry(enabled_tools=("access_tool",)),
                audit_dir=tmp_path / "audit",
                output_dir=tmp_path / "generated",
            )
        )

    assert error.value.missing_keys == ("user",)
    assert any("Intent detection task." in prompt for prompt in provider.prompts)
    assert not any("Plan creation task." in prompt for prompt in provider.prompts)
