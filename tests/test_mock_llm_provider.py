from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.engine.workflow_yaml import load_workflow_yaml
from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.models.llm import LLMRequest


def test_mock_llm_provider_returns_workflow_yaml():
    response = asyncio.run(
        MockLLMProvider().generate(
            LLMRequest(
                prompt="When critical router event happens, create alert and ServiceNow incident",
                model_name="mock-workflow-model",
            )
        )
    )

    assert response.provider == "mock"
    assert response.model_name == "mock-workflow-model"
    assert "workflow:" in response.text
    assert "description: When critical router event happens" in response.text


def test_mock_llm_provider_yaml_can_be_loaded_as_workflow():
    response = asyncio.run(
        MockLLMProvider().generate(
            LLMRequest(
                prompt="Create workflow",
                model_name="mock-workflow-model",
            )
        )
    )

    workflow = load_workflow_yaml(response.text)

    assert workflow.name == "critical_router_event_workflow"
    assert [step.tool for step in workflow.steps] == [
        "event_tool",
        "alert_tool",
        "servicenow_tool",
    ]
