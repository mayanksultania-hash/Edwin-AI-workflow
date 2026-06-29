"""Mock LLM provider for workflow generation."""

import json
import re

from ai_workflow.llm.base import BaseLLMProvider
from ai_workflow.models.llm import LLMRequest, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    provider_name = "mock"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        user_request = _extract_user_request(request.prompt)
        if "Intent detection task." in request.prompt:
            text = _build_mock_intent_json(user_request)
        elif "Plan creation task." in request.prompt:
            text = _build_mock_plan_json(user_request)
        elif "Generated code verification task." in request.prompt:
            text = _build_mock_code_verification_json()
        elif "Create an Action Group YAML for this request." in request.prompt:
            text = _build_mock_action_group_yaml()
        else:
            text = _build_mock_workflow_yaml(user_request)

        return LLMResponse(
            text=text,
            model_name=request.model_name,
            provider=self.provider_name,
        )


def _extract_user_request(prompt: str) -> str:
    marker = "User request:"
    if marker not in prompt:
        return prompt

    return prompt.split(marker, 1)[1].strip()


def _build_mock_intent_json(prompt: str) -> str:
    text = prompt.lower()
    if "access" in text:
        return json.dumps(
            {
                "name": "access_request",
                "domain": "identity_access",
                "summary": "Create an access workflow",
                "entities": _extract_access_entities(prompt),
            }
        )

    if "servicenow" in text or "incident" in text or "ticket" in text:
        return json.dumps(
            {
                "name": "incident_workflow",
                "domain": "it_service_management",
                "summary": "Create an incident or ticket workflow",
                "entities": {},
            }
        )

    return json.dumps(
        {
            "name": "general_workflow",
            "domain": "automation",
            "summary": "Create a general automation workflow",
            "entities": {},
        }
    )


def _build_mock_plan_json(prompt: str) -> str:
    entities = _extract_access_entities(prompt)
    if "access" in prompt.lower():
        user = entities.get("user", "target_user")
        system = entities.get("system", "target_system")
        return json.dumps(
            {
                "steps": [
                    {
                        "order": 1,
                        "goal": f"Request {system} access for {user}",
                        "tool": "access_tool",
                        "action": "request_access",
                        "inputs": {"user": user, "system": system},
                    },
                    {
                        "order": 2,
                        "goal": f"Grant {system} access after request is created",
                        "tool": "access_tool",
                        "action": "grant_access",
                        "inputs": {"request": "$steps.request_access.request"},
                    },
                ]
            }
        )

    return json.dumps(
        {
            "steps": [
                {
                    "order": 1,
                    "goal": "Check event details",
                    "tool": "event_tool",
                    "action": "match_event",
                    "inputs": {"severity": "critical", "source": "router"},
                },
                {
                    "order": 2,
                    "goal": "Create alert from event",
                    "tool": "alert_tool",
                    "action": "create_or_update_alert",
                    "inputs": {"event": "$steps.check_event.event"},
                },
                {
                    "order": 3,
                    "goal": "Create ServiceNow incident from alert",
                    "tool": "servicenow_tool",
                    "action": "create_incident",
                    "inputs": {"alert": "$steps.create_alert.alert"},
                },
            ]
        }
    )


def _extract_access_entities(prompt: str) -> dict[str, str]:
    entities: dict[str, str] = {}
    user_match = re.search(
        r"\b(?:give|grant)\s+([A-Z][a-zA-Z0-9._-]*)\b",
        prompt,
        re.IGNORECASE,
    )
    if user_match:
        entities["user"] = user_match.group(1)

    system_match = re.search(
        r"\b([A-Z][a-zA-Z0-9._-]*)\s+access\b",
        prompt,
        re.IGNORECASE,
    )
    if system_match:
        entities["system"] = system_match.group(1)

    return entities


def _build_mock_workflow_yaml(prompt: str) -> str:
    return f"""workflow:
  name: critical_router_event_workflow
  version: v0.1
  trigger:
    type: natural_language
    description: {prompt}
  steps:
    - id: check_event
      tool: event_tool
      action: match_event
      inputs:
        severity: critical
        source: router
    - id: create_alert
      tool: alert_tool
      action: create_or_update_alert
      inputs:
        event: $steps.check_event.event
    - id: notify_servicenow
      tool: servicenow_tool
      action: create_incident
      inputs:
        alert: $steps.create_alert.alert
"""


def _build_mock_action_group_yaml() -> str:
    return """action_group:
  name: Incident Processing v3.0
  description: Default action group to process ServiceNow incident updates sent from the LM-DX application
  source: sncIncident
  rule:
  steps:
    - order: 1
      id: lookup_incident_reference
      action_type: Lookup internal rowkey
      name: Lookup Incident reference
      description: Lookup Incident reference
    - order: 2
      id: store_incident_details_in_insight
      action_type: Update Insight
      name: Store Incident details in Insight
      description: Store Incident details in Insight
    - order: 3
      id: wait_if_incident_resolved_and_insight_active
      action_type: Delay Action Execution
      name: Wait for 5 min if Incident is Resolved and Insight is Active
      description: Wait for 5 min if Incident is Resolved and Insight is Active
      config:
        delay_minutes: 5
    - order: 4
      id: reopen_incident_if_insight_active
      action_type: Update SNC Incident
      name: Re-open Incident If Insight State is Active
      description: Re-open Incident If Insight State is Active
      start_condition:
        operator: AND
        conditions:
          - record: actionsystem
            field: Last Action Outcome
            operator: EQUALS
            value: Delay Completed
      mapped_fields:
        - target: State
          mappings:
            - type: value
              value: In Progress
    - order: 5
      id: store_incident_details_in_alert
      action_type: Update Alert
      name: Store Incident details in Alert
      description: Store Incident details in Alert
    - order: 6
      id: wait_if_incident_resolved_and_alert_active
      action_type: Delay Action Execution
      name: Wait for 5 min if Incident is Resolved and Alert is Active
      description: Wait for 5 min if Incident is Resolved and Alert is Active
      config:
        delay_minutes: 5
    - order: 7
      id: reopen_incident_if_singleton_alert_active
      action_type: Update SNC Incident
      name: Re-open Incident If Singleton Alert State is Active
      description: Re-open Incident If Singleton Alert State is Active
    - order: 8
      id: store_incident_details_in_additional_alerts
      action_type: Update Alert
      name: Store Incident details in additional Alerts
      description: Store Incident details in additional Alerts
      use_additional_records: true
"""


def _build_mock_code_verification_json() -> str:
    return json.dumps(
        {
            "approved": True,
            "risk_level": "low",
            "summary": "Generated code matches the workflow YAML and request.",
            "issues": [],
        }
    )
