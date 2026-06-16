from pathlib import Path
import asyncio
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.llm.mock_provider import MockLLMProvider
from ai_workflow.mcp.context_gatherer import MockMCPContextGatherer
from ai_workflow.orchestration.orchestrator_agent import OrchestratorAgent
from ai_workflow.tools.tool_manifest import build_default_tool_manifest


def build_agent():
    return OrchestratorAgent(
        llm_provider=MockLLMProvider(),
        model_name="mock-workflow-model",
        tool_manifest=build_default_tool_manifest(enabled_tools=("access_tool",)),
        max_output_tokens=800,
    )


def test_orchestrator_agent_detects_intent_with_llm():
    intent = asyncio.run(build_agent().detect_intent("Give John Tableau access"))

    assert intent.name == "access_request"
    assert intent.domain == "identity_access"
    assert intent.entities == {"user": "John", "system": "Tableau"}


def test_orchestrator_agent_creates_plan_with_llm():
    agent = build_agent()
    intent = asyncio.run(agent.detect_intent("Give John Tableau access"))
    context = asyncio.run(
        MockMCPContextGatherer().gather(
            user_request="Give John Tableau access",
            intent=intent,
            tool_manifest=agent.tool_manifest,
        )
    )

    plan = asyncio.run(
        agent.create_plan(
            user_request="Give John Tableau access",
            intent=intent,
            mcp_context=context,
        )
    )

    assert [step.action for step in plan.steps] == ["request_access", "grant_access"]
    assert plan.steps[0].inputs == {"user": "John", "system": "Tableau"}
