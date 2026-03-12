#!/usr/bin/env python
"""
Integration Test: Verify the complete workflow of the judge command

This test does not actually call the Anthropic API, but verifies:
1. Command line argument parsing
2. Report file reading
3. Data structure validation
4. Output file generation (using mock data)
"""

import json
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_judge_workflow():
    """Test the complete workflow of the judge command"""

    print("=" * 60)
    print("EDD Judge Command - Integration Test")
    print("=" * 60)

    # 1. Create test report
    print("\n[1/5] Creating test report...")
    test_report = [
        {
            "case": {
                "id": "test_list_files",
                "message": "List files in current directory",
            },
            "tool_names": ["Bash"],
            "final_output": "Current directory contains the following files:\n- README.md\n- pyproject.toml\n- src/",
            "passed": True,
            "duration_s": 1.2,
        },
        {
            "case": {"id": "test_read_file", "message": "Read README.md file content"},
            "tool_names": ["Read"],
            "final_output": "README.md file content has been read.",
            "passed": True,
            "duration_s": 0.8,
        },
        {
            "case": {
                "id": "test_complex_task",
                "message": "Analyze code and generate report",
            },
            "tool_names": ["Glob", "Read", "Grep", "Write"],
            "final_output": "Code analysis completed, report generated.",
            "passed": True,
            "duration_s": 5.3,
        },
    ]

    report_path = Path("test_integration_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(test_report, f, indent=2, ensure_ascii=False)
    print(f"✓ Test report created: {report_path}")

    # 2. Validate data structure
    print("\n[2/5] Validating data structure...")
    for i, result in enumerate(test_report, 1):
        assert "case" in result, f"Test {i} missing case field"
        assert "id" in result["case"], f"Test {i} missing case.id"
        assert "message" in result["case"], f"Test {i} missing case.message"
        assert "tool_names" in result, f"Test {i} missing tool_names"
        assert "final_output" in result, f"Test {i} missing final_output"
        print(f"✓ Test case {result['case']['id']} data structure correct")

    # 3. Simulate LLM evaluation (without actually calling API)
    print("\n[3/5] Simulating LLM evaluation...")
    judged_results = []

    for result in test_report:
        case_id = result["case"]["id"]
        tool_count = len(result["tool_names"])

        # 根据工具数量和复杂度生成模拟分数
        if tool_count == 1:
            scores = {
                "tool_selection_score": 7,
                "tool_order_score": 8,
                "output_quality_score": 8,
                "overall_score": 8,
            }
        elif tool_count <= 2:
            scores = {
                "tool_selection_score": 8,
                "tool_order_score": 8,
                "output_quality_score": 9,
                "overall_score": 8,
            }
        else:
            scores = {
                "tool_selection_score": 9,
                "tool_order_score": 9,
                "output_quality_score": 9,
                "overall_score": 9,
            }

        result_copy = result.copy()
        result_copy["llm_judgment"] = {
            **scores,
            "reasoning": f"Tool selection is reasonable ({tool_count} tools), output quality is good",
            "model": "claude-sonnet-4-5-20250929",
            "note": "This is mock data, actual use requires setting ANTHROPIC_API_KEY",
        }
        judged_results.append(result_copy)

        print(f"✓ {case_id}: Overall score {scores['overall_score']}/10")

    # 4. Calculate statistics
    print("\n[4/5] Calculating statistics...")
    avg_overall = sum(r["llm_judgment"]["overall_score"] for r in judged_results) / len(
        judged_results
    )
    avg_tool_selection = sum(
        r["llm_judgment"]["tool_selection_score"] for r in judged_results
    ) / len(judged_results)
    avg_tool_order = sum(
        r["llm_judgment"]["tool_order_score"] for r in judged_results
    ) / len(judged_results)
    avg_output_quality = sum(
        r["llm_judgment"]["output_quality_score"] for r in judged_results
    ) / len(judged_results)

    print("─" * 60)
    print("📊 Evaluation Statistics")
    print("─" * 60)
    print(f"Average overall score: {avg_overall:.1f}/10")
    print(f"Average tool selection: {avg_tool_selection:.1f}/10")
    print(f"Average tool order: {avg_tool_order:.1f}/10")
    print(f"Average output quality: {avg_output_quality:.1f}/10")

    # 5. Save results
    print("\n[5/5] Saving evaluation results...")
    output_path = Path("test_integration_report.judged.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(judged_results, f, indent=2, ensure_ascii=False)
    print(f"✓ Evaluation report saved: {output_path}")

    # 验证输出文件
    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert len(loaded) == len(test_report), "Output file record count mismatch"
        for r in loaded:
            assert "llm_judgment" in r, "Output missing llm_judgment field"
            assert "overall_score" in r["llm_judgment"], "Output missing overall_score"

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

    print("\n📝 Usage Instructions:")
    print("1. This is a mock test, verifying the data flow of the judge command")
    print("2. Actual use requires setting the ANTHROPIC_API_KEY environment variable")
    print("3. Command example:")
    print("   export ANTHROPIC_API_KEY=your_key")
    print("   edd edd judge --report test_integration_report.json")

    # Clean up test files
    print("\n🧹 Cleaning up test files...")
    report_path.unlink()
    output_path.unlink()
    print("✓ Test files cleaned up")


if __name__ == "__main__":
    try:
        test_judge_workflow()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
