"""Load values from a local env file."""

import os
from pathlib import Path
from typing import Optional

from ai_workflow.config.constants import DEFAULT_ENV_PATH


def load_env_file(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def get_env_value(name: str, env_path: Path = DEFAULT_ENV_PATH) -> Optional[str]:
    return os.environ.get(name) or load_env_file(env_path).get(name)
