"""File I/O helpers for LM Alert Processing customization."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml_text(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("LM Alert Processing YAML must be a mapping")
    return data


def dump_yaml_text(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def save_final_action_group_yaml(
    final_yaml: str,
    output_dir: Path,
) -> Path:
    output_path = output_dir / "lm_alert_processing" / "final.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_yaml, encoding="utf-8")
    return output_path
