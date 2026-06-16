"""Output path models for generated workflow files."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedOutputPaths:
    workflow_yaml_path: Path
    generated_code_path: Path
