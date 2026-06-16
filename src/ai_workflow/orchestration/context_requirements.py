"""Validate required runtime context before workflow generation."""

from dataclasses import dataclass

from ai_workflow.models.orchestration import Intent, MCPContext


ENTITY_ALIASES = {
    "access_type": "system",
    "resource": "system",
    "software": "system",
    "tool": "system",
}


@dataclass(frozen=True)
class MissingContextError(ValueError):
    missing_keys: tuple[str, ...]
    questions: tuple[str, ...]

    def __str__(self) -> str:
        return "Missing required context: " + ", ".join(self.missing_keys)


def validate_required_context(intent: Intent, mcp_context: MCPContext) -> None:
    required_keys = tuple(mcp_context.values.get("context_keys", ()))
    available_keys = set(context_from_intent(intent))
    missing_keys = tuple(key for key in required_keys if key not in available_keys)

    if missing_keys:
        raise MissingContextError(
            missing_keys=missing_keys,
            questions=tuple(_question_for_key(key) for key in missing_keys),
        )


def context_from_intent(intent: Intent) -> dict[str, str]:
    context: dict[str, str] = {}
    for key, value in intent.entities.items():
        if not isinstance(value, str):
            continue

        context[key] = value
        alias = ENTITY_ALIASES.get(key)
        if alias and alias not in context:
            context[alias] = value

    return context


def _question_for_key(key: str) -> str:
    questions = {
        "user": "Who should this workflow run for?",
        "system": "Which system or resource should this workflow use?",
    }
    return questions.get(key, f"What value should be used for {key}?")
