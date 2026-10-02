"""The two worked examples from the project specification, reproduced exactly.

The expected text below is copied from the specification.  The only addition
is the "Target Syntax Rule" line, which names the detected language.
"""

from pathlib import Path

from syntaxlens.analyzer import analyze
from syntaxlens.report.text import format_report
from syntaxlens.source import from_file

SAMPLES = Path(__file__).parent.parent / "samples"

EXAMPLE_1_REPORT = """\
============================================================
                SYNTACTICAL ANALYSIS REPORT
============================================================
Status: PASSED (0 Syntax Errors Found)
Total Lines Analyzed: 3
Target Syntax Rule: Python (auto-detected from the .py extension)

LINE BREAKDOWN & SYNTAX CHECK:
------------------------------------------------------------
Line 1: [x = 10]
  - Syntax Check: Variable Assignment -> OK
  - Delimiters: Balanced

Line 2: [if (x > 5):]
  - Syntax Check: Conditional Statement Header -> OK
  - Delimiters: Parentheses () Balanced | Colon ':' Present

Line 3: [print("Value is valid")]
  - Syntax Check: Function Call / Output Statement -> OK
  - Delimiters: Parentheses () Balanced | String Quotes "" Balanced

------------------------------------------------------------
SUMMARY:
  - Total Tokens Parsed: 14
  - Delimiter Balance: OK
  - Syntax Validation: SUCCESSFUL
============================================================"""

EXAMPLE_2_REPORT = """\
============================================================
                SYNTACTICAL ANALYSIS REPORT
============================================================
Status: FAILED (3 Syntax Errors Detected)
Total Lines Analyzed: 4
Target Syntax Rule: Python (auto-detected from the .py extension)

SYNTAX ERROR DETAILS:
------------------------------------------------------------
[ERROR 1] Line 2: if (x > 5
  - Category: Delimiter / Bracket Mismatch
  - Details: Unclosed parenthesis '('. Expected ')' before line end.

[ERROR 2] Line 3: print("Value is valid)
  - Category: String Literal Error
  - Details: Unclosed string literal. Missing matching double quote '"'.

[ERROR 3] Line 4: y = 20 + * 5
  - Category: Invalid Operator Sequence
  - Details: Consecutive binary operators '+ *' without an operand in between.

------------------------------------------------------------
SUMMARY:
  - Total Lines Checked: 4
  - Valid Lines: 1
  - Flagged Lines: 3 (Lines 2, 3, 4)
  - Action Required: Correct highlighted syntax errors above.
============================================================"""


def test_example_1_report_matches_the_specification():
    result = analyze(from_file(SAMPLES / "spec_example_1.py"))
    assert result.passed
    assert format_report(result) == EXAMPLE_1_REPORT


def test_example_2_report_matches_the_specification():
    result = analyze(from_file(SAMPLES / "spec_example_2.py"))
    assert [(error.line, error.code) for error in result.errors] == [
        (2, "E101"), (3, "E201"), (4, "E401"),
    ]
    assert format_report(result) == EXAMPLE_2_REPORT


def test_example_2_hides_follow_on_errors():
    """Line 2 also lacks its ':' and line 3's ')' is swallowed by the open string.

    Those are consequences of the real mistakes, so they are not reported.
    """
    result = analyze(from_file(SAMPLES / "spec_example_2.py"))
    assert len(result.diagnostics) == 3
