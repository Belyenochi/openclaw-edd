#!/usr/bin/env python
"""Test basic functionality of the judge command"""

import json
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from openclaw_edd.edd import cmd_judge


class Args:
    def __init__(self):
        self.report = "test_report.json"
        self.output = "test_report.judged.json"
        self.model = "claude-3-5-sonnet-20241022"


# Test argument parsing and basic workflow
args = Args()

# Check if report file exists
if not Path(args.report).exists():
    print(f"✗ Test report does not exist: {args.report}")
    sys.exit(1)

print("✓ Test report file exists")

# Read report
with open(args.report, "r", encoding="utf-8") as f:
    results = json.load(f)
    print(f"✓ Successfully read {len(results)} test results")

# Validate data structure
for result in results:
    assert "case" in result
    assert "id" in result["case"]
    assert "message" in result["case"]
    print(f"✓ Test case {result['case']['id']} data structure correct")

print("\n✓ All basic checks passed")
print(
    "\nNote: Actual LLM calls require setting the ANTHROPIC_API_KEY environment variable"
)
print("Usage: export ANTHROPIC_API_KEY=your_key && edd judge --report test_report.json")
