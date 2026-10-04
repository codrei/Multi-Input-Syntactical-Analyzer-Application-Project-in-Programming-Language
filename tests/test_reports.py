"""The detailed and classic text reports, the JSON report, and terminal colors."""

import json
from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze, analyze_text
from syntaxlens.console import RED, colorize, enable_colors
from syntaxlens.report.json_report import to_dict, to_json
from syntaxlens.report.text import format_report, pointer
from syntaxlens.source import from_file, from_text

SAMPLES = Path(__file__).parent.parent / "samples"


@pytest.fixture
def example_2():
    return analyze(from_file(SAMPLES / "spec_example_2.py"))


def test_classic_is_the_default_style(example_2):
    assert format_report(example_2) == format_report(example_2, "classic")
    assert "ERRORS BY CATEGORY" not in format_report(example_2)


def test_unknown_style_is_rejected(example_2):
    with pytest.raises(ValueError, match="Unknown report style"):
        format_report(example_2, "fancy")


def test_detailed_error_entry(example_2):
    report = format_report(example_2, "detailed")
    assert (
        "[ERROR 3] Line 4: y = 20 + * 5\n"
        "  - Category: Invalid Operator Sequence\n"
        "  - Details: Consecutive binary operators '+ *' without an operand in between.\n"
        "  - Location: line 4, column 10 (check 4: Operator Syntax, code E401)\n"
        "      4 | y = 20 + * 5\n"
        "        |          ^\n"
        "  - Fix: Remove one of the operators, or put a value between them.\n"
    ) in report


def test_detailed_keeps_every_classic_line(example_2):
    """The detailed style only adds lines; the specification's lines all remain, in order."""
    classic = format_report(example_2, "classic").split("\n")
    detailed = format_report(example_2, "detailed").split("\n")
    position = 0
    for line in classic:
        position = detailed.index(line, position) + 1


def test_detailed_has_totals_for_all_eight_checks_and_token_categories(example_2):
    report = format_report(example_2, "detailed")
    assert "  1. Delimiter & Bracket Matching ..............   1" in report
    assert "  3. Statement Terminators .....................   0" in report
    assert "  Total ........................................   3  (0 warnings)" in report
    assert "  Operators ..............   5  = (x2), >, +, *" in report
    assert "  Total Tokens Parsed ....  17" in report


def test_detailed_breakdown_points_to_the_errors(example_2):
    report = format_report(example_2, "detailed")
    assert "  - Syntax Check: Conditional Statement Header -> ERROR (see ERROR 1)" in report
    assert "  - Syntax Check: Variable Assignment -> OK" in report


def test_warnings_are_listed_but_do_not_fail():
    result = analyze_text("if (x = 5) {\n}\n", "java")
    report = format_report(result, "detailed")
    assert result.passed
    assert "Status: PASSED (0 Syntax Errors Found, 1 Warning)" in report
    assert "[WARNING 1] Line 1: if (x = 5) {" in report
    assert "-> WARNING (see WARNING 1)" in report


def test_pointer_lines_up_after_tabs():
    source = from_text("\tx = 1 +\n")
    assert pointer(source, 1, 8) == ["      1 |     x = 1 +", "        |           ^"]


def test_pointer_cuts_long_lines_around_the_column():
    source = from_text("total = " + " + ".join(["value"] * 40) + " + * 2\n")
    code_line, caret_line = pointer(source, 1, source.lines[0].index("* 2") + 1)
    assert code_line.startswith("      1 | ...")
    assert len(code_line) < 100
    assert code_line[caret_line.index("^")] == "*"


def test_json_report(example_2):
    data = json.loads(to_json(example_2))
    assert data["status"] == "FAILED"
    assert data["summary"]["flagged_lines"] == [2, 3, 4]
    assert data["summary"]["total_tokens"] == 17
    assert [d["code"] for d in data["diagnostics"]] == ["E101", "E201", "E401"]
    assert data["diagnostics"][2]["column"] == 10
    assert data["errors_by_check"][0] == {
        "check": 1, "title": "Delimiter & Bracket Matching", "errors": 1, "warnings": 0,
    }
    assert data["tokens_by_category"][1] == {
        "category": "Identifiers", "count": 4, "items": {"x": 2, "print": 1, "y": 1},
    }
    assert [line["status"] for line in data["lines"]] == ["ok", "error", "error", "error"]
    assert len(data["tokens"]) == 17


def test_json_for_valid_code():
    data = to_dict(analyze(from_file(SAMPLES / "spec_example_1.py")))
    assert data["status"] == "PASSED"
    assert data["language"]["detected_by"] == "extension"
    assert data["lines"][1]["delimiters"] == "Parentheses () Balanced | Colon ':' Present"


def test_colorize_marks_status_and_errors():
    text = "Status: FAILED (1 Syntax Error Detected)\n[ERROR 1] Line 1: x\nplain line"
    colored = colorize(text)
    assert colored.splitlines()[0].startswith("\033[1m" + RED)
    assert colored.splitlines()[2] == "plain line"


def test_colors_are_off_when_not_a_terminal(tmp_path, monkeypatch):
    with open(tmp_path / "out.txt", "w") as stream:
        assert enable_colors(stream) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert enable_colors(disabled=False) is False
