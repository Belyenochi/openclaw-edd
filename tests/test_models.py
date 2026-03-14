from unittest.mock import patch

import pytest

from openclaw_edd import eval as eval_module
from openclaw_edd.models import EvalCase, EvalResult, Event


def _make_result(case, passed):
    return EvalResult(
        case=case,
        passed=passed,
        events=[],
        final_output="",
        duration_s=1.0,
        session_id="sess-" + ("pass" if passed else "fail"),
        total_input_tokens=10,
        total_output_tokens=5,
        total_cost=0.001,
    )


def test_pass_at_k_all_pass():
    case = EvalCase(id="c1", message="hi", pass_at_k=3)
    with patch.object(
        eval_module,
        "run_eval_case",
        side_effect=[
            _make_result(case, True),
            _make_result(case, True),
            _make_result(case, True),
        ],
    ):
        result = eval_module.run_eval_case_pass_at_k(case, 3, True, "/tmp")
    assert result.passed is True
    assert result.pass_at_k_k == 3
    assert result.pass_at_k_passes == 3
    assert result.pass_at_k_rate == 1.0


def test_pass_at_k_partial_pass():
    case = EvalCase(id="c2", message="hi", pass_at_k=3)
    with patch.object(
        eval_module,
        "run_eval_case",
        side_effect=[
            _make_result(case, False),
            _make_result(case, True),
            _make_result(case, False),
        ],
    ):
        result = eval_module.run_eval_case_pass_at_k(case, 3, True, "/tmp")
    assert result.passed is True
    assert result.pass_at_k_passes == 1
    assert abs(result.pass_at_k_rate - 1 / 3) < 1e-9
    assert result.total_cost == pytest.approx(0.003)


def test_pass_at_k_all_fail():
    case = EvalCase(id="c3", message="hi", pass_at_k=3)
    with patch.object(
        eval_module,
        "run_eval_case",
        side_effect=[
            _make_result(case, False),
            _make_result(case, False),
            _make_result(case, False),
        ],
    ):
        result = eval_module.run_eval_case_pass_at_k(case, 3, True, "/tmp")
    assert result.passed is False
    assert result.pass_at_k_passes == 0
    assert result.pass_at_k_rate == 0.0


def test_pass_at_k_aggregates_cost():
    case = EvalCase(id="c4", message="hi")
    with patch.object(
        eval_module,
        "run_eval_case",
        side_effect=[
            _make_result(case, True),
            _make_result(case, False),
        ],
    ):
        result = eval_module.run_eval_case_pass_at_k(case, 2, True, "/tmp")
    assert result.total_input_tokens == 20
    assert result.total_output_tokens == 10
    assert result.total_cost == pytest.approx(0.002)
    assert len(result.pass_at_k_session_ids) == 2


def test_event_to_dict_filters_empty_values():
    event = Event(kind="tool_end", tool="exec")
    data = event.to_dict()
    assert data["kind"] == "tool_end"
    assert data["tool"] == "exec"
    assert "output" not in data


def test_eval_result_tool_names():
    event = Event(kind="tool_end", tool="exec")
    case = EvalCase(id="c1", message="hi")
    result = EvalResult(
        case=case,
        passed=True,
        events=[event],
        final_output="ok",
        duration_s=0.1,
    )
    assert result.tool_names == ["exec"]
