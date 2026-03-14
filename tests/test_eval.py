from datetime import datetime, timedelta, timezone

from openclaw_edd import eval as eval_module
from openclaw_edd.models import EvalCase, Event


def _ev(tool, command, ts):
    return Event(
        kind="tool_end",
        tool=tool,
        input={"command": command},
        output="",
        duration_ms=1,
        ts=ts,
        session_id="s",
    )


def test_expect_commands_matching():
    events = [
        _ev(
            "exec",
            "curl -s https://example.com/weather?city=Tokyo",
            "2026-03-01T01:00:00Z",
        )
    ]
    case = EvalCase(
        id="cmd_match",
        message="",
        expect_commands=["curl", "tokyo"],
    )
    passed, failures, checks = eval_module.check_assertions(
        case, events, "Tokyo weather"
    )
    assert passed
    assert failures == []
    assert checks["commands"]["passed"] is True


def test_forbidden_commands():
    events = [_ev("exec", "rm -rf /", "2026-03-01T01:00:00Z")]
    case = EvalCase(
        id="forbid",
        message="",
        forbidden_commands=["rm -rf /"],
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert not passed
    assert not passed and len(failures) > 0
    assert checks["forbidden_commands"]["passed"] is False


def test_commands_ordered():
    events = [
        _ev("exec", "ls", "2026-03-01T01:00:00Z"),
        _ev("exec", "wc -l", "2026-03-01T01:00:01Z"),
    ]
    case = EvalCase(
        id="ordered",
        message="",
        expect_commands_ordered=["ls", "wc"],
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert passed
    assert checks["commands_ordered"]["passed"] is True


def test_expect_tool_args_substring():
    events = [
        _ev(
            "exec",
            "bash ./skills/ceresdb/scripts/check_health.sh prod-01",
            "2026-03-01T01:00:00Z",
        )
    ]
    case = EvalCase(
        id="tool_args",
        message="",
        expect_tool_args={"exec": {"command": "check_health"}},
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert passed
    assert checks["tool_args"]["passed"] is True


def test_session_isolation_time_window():
    base = datetime(2026, 3, 1, 1, 0, 0, tzinfo=timezone.utc)
    events = [
        _ev("exec", "old", (base - timedelta(seconds=10)).isoformat()),
        _ev("exec", "inside", (base + timedelta(seconds=1)).isoformat()),
        _ev("exec", "new", (base + timedelta(seconds=10)).isoformat()),
    ]
    start_dt = base
    end_dt = base + timedelta(seconds=5)
    filtered = eval_module._filter_events_by_time(events, start_dt, end_dt)
    cmds = [e.input.get("command") for e in filtered]
    assert "inside" in cmds
    assert "old" not in cmds
    assert "new" not in cmds


def test_plan_contains_pass():
    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "curl -s https://api.open-meteo.com/..."},
            plan_text="I'll check the weather in Shanghai using the API",
        ),
    ]
    case = EvalCase(
        id="plan_test",
        message="",
        expect_plan_contains=["weather", "shanghai"],
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert passed
    assert checks["plan_contains"]["passed"]


def test_plan_contains_missing():
    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "curl -s https://api.open-meteo.com/..."},
            plan_text="Let me query the API",
        ),
    ]
    case = EvalCase(
        id="plan_test",
        message="",
        expect_plan_contains=["weather"],
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert not passed


def test_plan_contains_no_plan():
    events = [
        Event(kind="tool_end", tool="exec", input={"command": "ls"}),
    ]
    case = EvalCase(
        id="plan_test",
        message="",
        expect_plan_contains=["list"],
    )
    passed, failures, checks = eval_module.check_assertions(case, events, "")
    assert not passed
    assert checks["plan_contains"]["reason"] == "no_plan_text_found"


# ---------------------------------------------------------------------------
# load_cases with only_approved filter
# ---------------------------------------------------------------------------


def _write_jsonl(path: str, records: list) -> None:
    import json

    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def test_load_cases_only_approved_filters(tmp_path):
    from openclaw_edd import eval as eval_module

    records = [
        {
            "id": "r1",
            "reviewed": True,
            "approved": True,
            "conversation": [{"turn": 1, "user": "approved msg", "assert": []}],
        },
        {
            "id": "r2",
            "reviewed": True,
            "approved": False,
            "conversation": [{"turn": 1, "user": "rejected msg", "assert": []}],
        },
        {
            "id": "r3",
            "reviewed": False,
            "conversation": [{"turn": 1, "user": "unreviewed msg", "assert": []}],
        },
    ]
    f = tmp_path / "golden.jsonl"
    _write_jsonl(str(f), records)

    cases = eval_module.load_cases(str(f), only_approved=True)
    assert len(cases) == 1
    assert cases[0].message == "approved msg"


def test_load_cases_without_only_approved_loads_all(tmp_path):
    from openclaw_edd import eval as eval_module

    records = [
        {
            "id": "r1",
            "reviewed": True,
            "approved": True,
            "conversation": [{"turn": 1, "user": "msg1", "assert": []}],
        },
        {
            "id": "r2",
            "reviewed": False,
            "conversation": [{"turn": 1, "user": "msg2", "assert": []}],
        },
    ]
    f = tmp_path / "golden.jsonl"
    _write_jsonl(str(f), records)

    cases = eval_module.load_cases(str(f), only_approved=False)
    assert len(cases) == 2
