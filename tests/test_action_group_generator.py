from pathlib import Path
import asyncio
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.action_group_validator import ActionGroupValidatorError
from ai_workflow.generator.action_group_generator import ActionGroupGenerator
from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.models.llm import LLMResponse


def test_action_group_generator_uses_mock_llm_response():
    action_group = asyncio.run(
        ActionGroupGenerator(
            llm_provider=MockLLMProvider(),
            model_name="mock-action-group-model",
        ).generate(
            "Create an action group for ServiceNow incident updates"
        )
    )

    assert action_group.name == "Incident Processing v3.0"
    assert action_group.source == "sncIncident"
    assert [step.action_type for step in action_group.steps] == [
        "Lookup internal rowkey",
        "Update Insight",
        "Delay Action Execution",
        "Update SNC Incident",
        "Update Alert",
        "Delay Action Execution",
        "Update SNC Incident",
        "Update Alert",
    ]


class CapturingActionGroupLLMProvider(BaseLLMProvider):
    provider_name = "capturing"

    def __init__(self):
        self.last_prompt = None
        self.last_max_output_tokens = None

    async def generate(self, request):
        self.last_prompt = request.prompt
        self.last_max_output_tokens = request.max_output_tokens
        return LLMResponse(
            text="""action_group:
  name: Captured Action Group
  description: Captured Action Group
  source: insights
  rule:
  steps:
    - order: 1
      id: update_insight
      action_type: Update Insight
      name: Update Insight
      description: Update Insight
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_action_group_generator_sends_action_ui_prompt_to_llm():
    provider = CapturingActionGroupLLMProvider()

    asyncio.run(
        ActionGroupGenerator(
            llm_provider=provider,
            model_name="test-model",
            max_output_tokens=900,
        ).generate("Create a simple insight action group")
    )

    assert "Create an Action Group YAML for this request." in provider.last_prompt
    assert "General, ordered Actions, Start Condition, Stop condition" in provider.last_prompt
    assert "- Update Insight" in provider.last_prompt
    assert "- sncIncident" in provider.last_prompt
    assert "Create a simple insight action group" in provider.last_prompt
    assert provider.last_max_output_tokens == 900


class InvalidActionGroupLLMProvider(BaseLLMProvider):
    provider_name = "invalid"

    async def generate(self, request):
        return LLMResponse(
            text="""action_group:
  name: Invalid Action Group
  description: Invalid Action Group
  source: insights
  rule:
  steps:
    - order: 1
      id: invalid_step
      action_type: Made Up Action
      name: Invalid Step
      description: Invalid Step
""",
            model_name=request.model_name,
            provider=self.provider_name,
        )


def test_action_group_generator_validates_llm_yaml_against_action_ui_context():
    with pytest.raises(ActionGroupValidatorError, match="unknown action type"):
        asyncio.run(
            ActionGroupGenerator(
                llm_provider=InvalidActionGroupLLMProvider(),
                model_name="test-model",
            ).generate("Create invalid action group")
        )
