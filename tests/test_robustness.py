"""The analyzer must never crash, whatever it is given, and must stay fast."""

import random
import time
from pathlib import Path

from syntaxlens.analyzer import analyze_text
from syntaxlens.report.text import format_report

PIECES = [
    "x", "y", "if", "else", "elif", "for", "in", "while", "def", "class", "return", "break",
    "int", "String", "case", "switch", "default", "do", "new", "lambda", "not", "and",
    "(", ")", "[", "]", "{", "}", ":", ";", ",", ".", "=", "==", "+", "-", "*", "**", "/",
    "->", "?", "!", "&&", "<", ">", ">>", "@", "1", "2.5", "0x1F", "09", '"s"', "'c'",
    '"open', "'", '"""', "/*", "*/", "//c", "#c", "\n", "\n    ", "\n\t", " ", "$",
    "\u201c", "\u00a0", "\\",
]


def test_random_input_never_crashes():
    rng = random.Random(2026)
    for _ in range(2000):
        code = "".join(rng.choice(PIECES) + rng.choice(["", " "]) for _ in range(rng.randint(1, 40)))
        for language in ("python", "java"):
            format_report(analyze_text(code, language))  # must not raise


def test_ten_thousand_lines_in_well_under_two_seconds():
    corpus = Path(__file__).parent / "data" / "python_valid"
    program = "\n".join(path.read_text(encoding="utf-8") for path in sorted(corpus.glob("*.py")))
    lines = (program + "\n").split("\n")
    code = "\n".join((lines * (10_000 // len(lines) + 1))[:9_999] + ["done = True"])
    started = time.perf_counter()
    result = analyze_text(code, "python")
    assert time.perf_counter() - started < 2.0
    assert result.source.line_count == 10_000
    assert result.passed
