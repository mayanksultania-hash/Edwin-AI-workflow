"""Load Action Group step-group metadata for LM Alert Processing.

YAML layout:
- ``lm_alert_processing_step_groups.yaml`` — workflow stages, step names, guided questions
"""

from functools import lru_cache
from pathlib import Path

import yaml

from ai_workflow.action_groups.common.action_schemas.base import (
    StepGroupDescription,
    render_step_group_prompt_context,
)

_CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_STEP_GROUPS_PATH = _CONFIG_DIR / "lm_alert_processing_step_groups.yaml"


class LMAlertActionGroupStepGroupConfig:
    """Load step groups for the LM Alert Processing action group."""

    def __init__(self, config_path: Path = DEFAULT_STEP_GROUPS_PATH) -> None:
        self.config_path = config_path

    def load(self) -> list[StepGroupDescription]:
        if not self.config_path.is_file():
            raise FileNotFoundError(
                f"Action group step groups config not found: {self.config_path}"
            )

        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        groups = raw.get("step_groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError(
                f"Action group step groups must contain a non-empty 'step_groups' list: "
                f"{self.config_path}"
            )

        return [StepGroupDescription.model_validate(group) for group in groups]


@lru_cache(maxsize=1)
def _cached_lm_alert_action_group_step_groups() -> tuple[StepGroupDescription, ...]:
    return tuple(LMAlertActionGroupStepGroupConfig().load())


def build_lm_alert_action_group_step_groups() -> list[StepGroupDescription]:
    """Return step groups for the LM Alert Processing action group."""

    return list(_cached_lm_alert_action_group_step_groups())


def build_lm_alert_action_group_step_group_prompt_context() -> str:
    """Return compact action-group step guidance for LM Alert prompts."""

    return render_step_group_prompt_context(build_lm_alert_action_group_step_groups())


# Backward-compatible aliases.
build_lm_alert_step_groups = build_lm_alert_action_group_step_groups
build_lm_alert_step_group_prompt_context = build_lm_alert_action_group_step_group_prompt_context
