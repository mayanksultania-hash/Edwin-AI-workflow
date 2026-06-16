from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

import pytest

from ai_workflow.engine.input_resolver import InputResolutionError, resolve_step_inputs
from ai_workflow.models.workflow import Step


def test_resolve_step_inputs_merges_previous_data_and_step_inputs():
    step = Step(
        id="create_alert",
        tool="alert_tool",
        action="create_or_update_alert",
        inputs={"severity": "critical"},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={"event": {"source": "router"}},
        step_outputs={},
        context={},
    )

    assert inputs == {
        "event": {"source": "router"},
        "severity": "critical",
    }


def test_resolve_step_inputs_prefers_explicit_step_inputs():
    step = Step(
        id="check_event",
        tool="event_tool",
        action="match_event",
        inputs={"severity": "critical"},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={"severity": "warning"},
        step_outputs={},
        context={},
    )

    assert inputs["severity"] == "critical"


def test_resolve_step_inputs_accepts_future_reference_context():
    step = Step(
        id="notify_servicenow",
        tool="servicenow_tool",
        action="create_incident",
        inputs={},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={"alert": {"id": "alert-1"}},
        step_outputs={"create_alert": {"alert": {"id": "alert-1"}}},
        context={"request_id": "req-1"},
    )

    assert inputs == {"alert": {"id": "alert-1"}}


def test_resolve_step_inputs_reads_step_reference():
    step = Step(
        id="create_alert",
        tool="alert_tool",
        action="create_or_update_alert",
        inputs={"event": "$steps.check_event.event"},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={},
        step_outputs={"check_event": {"event": {"source": "router"}}},
        context={},
    )

    assert inputs == {"event": {"source": "router"}}


def test_resolve_step_inputs_reads_context_reference():
    step = Step(
        id="notify",
        tool="servicenow_tool",
        action="create_incident",
        inputs={"request_id": "$context.request_id"},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={},
        step_outputs={},
        context={"request_id": "req-1"},
    )

    assert inputs == {"request_id": "req-1"}


def test_resolve_step_inputs_reads_nested_reference_values():
    step = Step(
        id="notify",
        tool="servicenow_tool",
        action="create_incident",
        inputs={"payload": {"alert": "$steps.create_alert.alert"}},
    )

    inputs = resolve_step_inputs(
        step=step,
        previous_data={},
        step_outputs={"create_alert": {"alert": {"id": "alert-1"}}},
        context={},
    )

    assert inputs == {"payload": {"alert": {"id": "alert-1"}}}


def test_resolve_step_inputs_rejects_missing_reference():
    step = Step(
        id="create_alert",
        tool="alert_tool",
        action="create_or_update_alert",
        inputs={"event": "$steps.missing.event"},
    )

    with pytest.raises(InputResolutionError, match="Cannot resolve input reference"):
        resolve_step_inputs(
            step=step,
            previous_data={},
            step_outputs={},
            context={},
        )
