"""Tests for LLM judge integration."""

from unittest.mock import MagicMock, patch

from openclaw_edd.judge import build_judge_prompt, judge_case
from openclaw_edd.models import EvalCase, Event


def test_build_judge_prompt_structure():
    case = EvalCase(id="test", message="Check MySQL", judge_criteria=["Is it correct?"])
    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "mysql -e 'SHOW PROCESSLIST'"},
            plan_text="I'll check running queries",
        ),
    ]
    prompt = build_judge_prompt(
        case, events, "Found 3 slow queries", ["Is it correct?"]
    )
    assert "Check MySQL" in prompt
    assert "SHOW PROCESSLIST" in prompt
    assert "Found 3 slow queries" in prompt
    assert "Is it correct?" in prompt


def test_judge_case_no_config():
    """Judge should return empty dict if not configured."""
    case = EvalCase(id="test", message="hi")
    result = judge_case(case, [], "hello")
    assert result == {}


@patch("openclaw_edd.judge.call_judge")
def test_judge_case_with_mock(mock_call):
    mock_call.return_value = {
        "overall_pass": True,
        "overall_score": 0.9,
        "scores": {"criterion_1": 0.9},
        "reasoning": "Good job",
    }
    case = EvalCase(
        id="test",
        message="check db",
        judge_criteria=["Is diagnosis correct?"],
        judge_model="kimi-k2.5",
        judge_provider="moonshot",
    )
    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "mysql -e 'SELECT 1'"},
        )
    ]
    result = judge_case(case, events, "Database is healthy")
    assert result["passed"] is True
    assert result["overall_score"] == 0.9


def test_judge_integration_in_check_assertions():
    """Test that judge is called when judge_criteria and judge_model are set."""
    from openclaw_edd.eval import check_assertions

    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "ls -la"},
            plan_text="I'll list the files",
        ),
    ]
    case = EvalCase(
        id="judge_test",
        message="List files",
        judge_criteria=["Did the agent list files correctly?"],
        judge_model="gpt-4",
        judge_provider="openai",
    )

    with patch("openclaw_edd.judge.call_judge") as mock_call:
        mock_call.return_value = {
            "overall_pass": True,
            "overall_score": 0.95,
            "scores": {"criterion_1": 0.95},
            "reasoning": "Agent listed files correctly",
        }
        passed, failures, checks = check_assertions(case, events, "Here are the files")

    assert "judge" in checks
    assert checks["judge"]["passed"] is True


def test_judge_soft_fail_when_rule_fail_but_judge_pass():
    """Test soft_fail flag when rules fail but judge passes."""
    from openclaw_edd.eval import check_assertions

    events = [
        Event(
            kind="tool_end",
            tool="exec",
            input={"command": "ls -la"},
            plan_text="I'll list the files",
        ),
    ]
    case = EvalCase(
        id="judge_test",
        message="List files",
        expect_tools=["exec", "read"],  # This will fail (missing "read")
        judge_criteria=["Did the agent list files correctly?"],
        judge_model="gpt-4",
        judge_provider="openai",
    )

    with patch("openclaw_edd.judge.call_judge") as mock_call:
        mock_call.return_value = {
            "overall_pass": True,
            "overall_score": 0.95,
            "scores": {"criterion_1": 0.95},
            "reasoning": "Agent listed files correctly",
        }
        passed, failures, checks = check_assertions(case, events, "Here are the files")

    assert not passed  # Still fails due to missing "read" tool
    assert "judge" in checks
    assert checks["judge"].get("soft_fail") is True
    assert "hint" in checks["judge"]
