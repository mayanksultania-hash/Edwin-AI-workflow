from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from ai_workflow.prompting.template_renderer import render_prompt_template


def test_render_prompt_template_renders_jinja_file():
    prompt = render_prompt_template(
        "orchestration/templates/intent_detection.j2",
        {"user_request": "Give John Tableau access"},
    )

    assert "Intent detection task." in prompt
    assert "User request:" in prompt
    assert "Give John Tableau access" in prompt
