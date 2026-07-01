"""Pydantic models for LM Alert Processing LLM structured output."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GuidedQuestionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    question: str
    example_answer: str = ""


class GuidedQuestionsOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[GuidedQuestionModel] = Field(min_length=1, max_length=12)


class ConditionPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    operator: str
    value: Any = None
    value_type: str = "string"


class SetGroupNamePatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_group_name"]
    value: str


class SetGroupDescriptionPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_group_description"]
    value: str


class SetDelaySecondsPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_delay_seconds"]
    step_name: str
    value: int = Field(ge=0)


class SetActionConfigValuePatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_action_config_value"]
    step_name: str
    config_name: str
    value: Any


class SetMappingValuePatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_mapping_value"]
    step_name: str
    target: str
    value: Any


class SetStepPreconditionPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["set_step_precondition"]
    step_name: str
    combinator: Literal["AND", "OR"] = "AND"
    conditions: list[ConditionPatchModel] = Field(min_length=1)


class AddStepPreconditionConditionsPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["add_step_precondition_conditions"]
    step_name: str
    combinator: Literal["AND", "OR"] = "AND"
    conditions: list[ConditionPatchModel] = Field(min_length=1)


class RemoveStepPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["remove_step"]
    step_name: str


YamlPatchModel = Annotated[
    SetGroupNamePatchModel
    | SetGroupDescriptionPatchModel
    | SetDelaySecondsPatchModel
    | SetActionConfigValuePatchModel
    | SetMappingValuePatchModel
    | SetStepPreconditionPatchModel
    | AddStepPreconditionConditionsPatchModel
    | RemoveStepPatchModel,
    Field(discriminator="type"),
]


class YamlPatchPlanOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    patches: list[YamlPatchModel]
