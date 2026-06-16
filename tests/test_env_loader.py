from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.config.env import get_env_value, load_env_file


def test_load_env_file_reads_key_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
# local secrets
OPENAI_API_KEY=test-key
OTHER_VALUE="quoted"
""",
        encoding="utf-8",
    )

    values = load_env_file(env_path)

    assert values["OPENAI_API_KEY"] == "test-key"
    assert values["OTHER_VALUE"] == "quoted"


def test_load_env_file_returns_empty_when_missing(tmp_path):
    assert load_env_file(tmp_path / ".env") == {}


def test_get_env_value_prefers_process_env(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "process-key")

    assert get_env_value("OPENAI_API_KEY", env_path) == "process-key"


def test_get_env_value_reads_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert get_env_value("OPENAI_API_KEY", env_path) == "file-key"
