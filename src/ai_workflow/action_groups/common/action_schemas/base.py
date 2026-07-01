"""Base models for Action ID schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionFieldDescription(BaseModel):
    """A field the LLM may customize."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Exact field name to use in patches.")
    description: str = Field(description="Simple explanation of the field.")
    example: Any = Field(default=None, description="Small example value.")


class ActionSchemaDescription(BaseModel):
    """Description of one reusable Action type."""

    model_config = ConfigDict(extra="forbid")

    action_name: str = Field(description="UI action name.")
    action_id: str | None = Field(default=None, description="Action Service action ID.")
    use_for: str = Field(description="When this action type is used.")
    patch_guidance: str = Field(description="Which patch type should usually modify it.")
    action_config_fields: list[ActionFieldDescription] = Field(default_factory=list)
    mapping_fields: list[ActionFieldDescription] = Field(default_factory=list)
    precondition_fields: list[ActionFieldDescription] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class StepGroupQuestionHint(BaseModel):
    """One suggested guided-setup question for a step group."""

    model_config = ConfigDict(extra="forbid")

    key_suffix: str = Field(description="Snake_case suffix appended to the group_id.")
    question: str = Field(description="Customer-facing question for this topic.")
    example_answer: str = Field(default="", description="Short placeholder hint for the answer.")


class StepGroupDescription(BaseModel):
    """A group of related workflow steps the user can answer about together."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(description="Stable snake_case key for this step group.")
    label: str = Field(description="Short human label, for example 'Steps 1-5: Alert path'.")
    purpose: str = Field(description="What this group of steps does in plain English.")
    step_names: list[str] = Field(
        default_factory=list,
        description="Exact step names that belong to this group.",
    )
    patchable_areas: list[str] = Field(
        default_factory=list,
        description="What can be customized here, for example preconditions, mappings, delays.",
    )
    question_hints: list[StepGroupQuestionHint] = Field(
        min_length=1,
        max_length=2,
        description="Up to two specific questions the LLM may ask for this group.",
    )


def step_group_question_key(group_id: str, key_suffix: str) -> str:
    """Return the canonical guided-question key for one group topic."""

    return f"{group_id}__{key_suffix}"


def extract_group_id_from_question_key(
    key: str,
    known_group_ids: set[str] | None = None,
) -> str | None:
    """Return the step group id encoded in a guided-question key, if any."""

    if "__" in key:
        group_id = key.split("__", 1)[0]
        if known_group_ids is None or group_id in known_group_ids:
            return group_id
        return None

    if known_group_ids and key in known_group_ids:
        return key

    return None


def render_step_group_prompt_context(groups: list[StepGroupDescription]) -> str:
    """Render step groups as compact prompt context."""

    lines: list[str] = []
    for group in groups:
        lines.append(f"- {group.label} [{group.group_id}]")
        lines.append(f"  Purpose: {group.purpose}")
        if group.patchable_areas:
            lines.append(f"  Customizable: {', '.join(group.patchable_areas)}")
        lines.append("  Suggested questions (ask up to 2 from this group):")
        for hint in group.question_hints:
            lines.append(
                f"    - key: {step_group_question_key(group.group_id, hint.key_suffix)}"
            )
            lines.append(f"      question: {hint.question}")
            if hint.example_answer:
                lines.append(f"      example_answer: {hint.example_answer}")
        if group.step_names:
            lines.append("  Steps:")
            for step_name in group.step_names:
                lines.append(f"    - {step_name}")

    return "\n".join(lines)


def render_action_schema_prompt_context(
    schemas: list[ActionSchemaDescription],
) -> str:
    """Render action schemas as compact prompt context."""

    lines: list[str] = []
    for schema in schemas:
        action_id = f" ({schema.action_id})" if schema.action_id else ""
        lines.append(f"- {schema.action_name}{action_id}")
        lines.append(f"  Use for: {schema.use_for}")
        lines.append(f"  Patch guidance: {schema.patch_guidance}")

        if schema.mapping_fields:
            lines.append("  Mapping fields:")
            for field in schema.mapping_fields:
                lines.append(
                    f"    - {field.name}: {field.description} Example: {field.example}"
                )

        if schema.action_config_fields:
            lines.append("  Action config fields:")
            for field in schema.action_config_fields:
                lines.append(
                    f"    - {field.name}: {field.description} Example: {field.example}"
                )

        if schema.precondition_fields:
            lines.append("  Precondition fields:")
            for field in schema.precondition_fields:
                lines.append(
                    f"    - {field.name}: {field.description} Example: {field.example}"
                )

        if schema.examples:
            lines.append("  Examples:")
            for example in schema.examples:
                lines.append(f"    - {example}")

    return "\n".join(lines)
