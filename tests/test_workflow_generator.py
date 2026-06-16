from pathlib import Path
import asyncio
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.generator.workflow_generator import generate_workflow
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.models.llm import LLMResponse
from ai_workflow.models.tool_manifest import ToolActionManifest, ToolManifest
from ai_workflow.models.workflow import WorkflowValidationError


def test_generate_workflow_uses_llm_provider_response():
    workflow = asyncio.run(
        generate_workflow(
            prompt="When critical router event happens, create alert and incident",
            model_name="mock-workflow-model",
            llm_provider=MockLLMProvider(),
        )
    )

    assert workflow.name == "critical_router_event_workflow"
    assert workflow.trigger.description == (
        "When critical router event happens, create alert and incident"
    )
    assert [step.id for step in workflow.steps] == [
        "check_event",
        "create_alert",
        "notify_servicenow",
    ]


def test_generate_workflow_returns_validated_workflow():
    workflow = asyncio.run(
        generate_workflow(
            prompt="Create workflow",
            model_name="mock-workflow-model",
            llm_provider=MockLLMProvider(),
        )
    )

    assert workflow.steps[0].tool == "event_tool"
    assert workflow.steps[1].tool == "alert_tool"
    assert workflow.steps[2].tool == "servicenow_tool"


class BadLLMProvider(BaseLLMProvider):
    provider_name = "bad"

    async def generate(self, request):
        return LLMResponse(
            text="workflow:\n  name: broken\n",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_generate_workflow_raises_when_llm_returns_invalid_yaml():
    with pytest.raises(WorkflowValidationError):
        asyncio.run(
            generate_workflow(
                prompt="bad workflow",
                model_name="bad-model",
                llm_provider=BadLLMProvider(),
            )
        )


class CapturingLLMProvider(BaseLLMProvider):
    provider_name = "capturing"

    def __init__(self):
        self.last_prompt = None

    async def generate(self, request):
        self.last_prompt = request.prompt
        return LLMResponse(
            text="""workflow:
  name: captured_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: captured
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_generate_workflow_sends_built_prompt_to_llm():
    provider = CapturingLLMProvider()

    asyncio.run(
        generate_workflow(
            prompt="Create alert workflow",
            model_name="test-model",
            llm_provider=provider,
        )
    )

    assert "Return only YAML." in provider.last_prompt
    assert "event_tool.match_event" in provider.last_prompt
    assert "Create alert workflow" in provider.last_prompt


def test_generate_workflow_sends_configured_tool_manifest_to_llm():
    provider = CapturingLLMProvider()
    manifest = ToolManifest(
        actions=(
            ToolActionManifest(tool="custom_tool", action="custom_action"),
        )
    )

    asyncio.run(
        generate_workflow(
            prompt="Create custom workflow",
            model_name="test-model",
            llm_provider=provider,
            tool_manifest=manifest,
        )
    )

    assert "custom_tool.custom_action" in provider.last_prompt
    assert "servicenow_tool.create_incident" not in provider.last_prompt
