from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_defines_cli_entrypoint():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["ai-workflow"] == "ai_workflow.main:main"


def test_pyproject_uses_src_package_layout():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_pyproject_includes_jinja_dependency():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "jinja2>=3.1.0" in data["project"]["dependencies"]


def test_pyproject_includes_prompt_templates_as_package_data():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["tool"]["setuptools"]["package-data"]["ai_workflow"] == ["**/*.j2"]
