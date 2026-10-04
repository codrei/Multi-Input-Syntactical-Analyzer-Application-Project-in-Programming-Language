"""JSON reports: the analysis result as data, for other programs.

The web app (Phase 5) receives exactly this structure from the server, and
``syntaxlens file code.py --format json`` prints it.  Everything in the text
report is here too, plus every token.  (The module is called json_report.py so
it is never confused with Python's built-in json module.)
"""

from __future__ import annotations

import json
from collections import Counter

from .. import __version__
from ..analyzer import AnalysisResult
from ..diagnostics import Check, Diagnostic
from ..tokens import group_by_category


def to_dict(result: AnalysisResult) -> dict:
    """The whole analysis as plain dictionaries and lists."""
    source = result.source
    flagged = result.flagged_lines
    return {
        "tool": {"name": "SyntaxLens", "version": __version__},
        "source": {
            "name": source.name,
            "lines": source.line_count,
            "encoding": source.encoding,
            "line_endings": source.newline_style,
        },
        "language": {
            "key": result.detection.profile.key,
            "name": result.detection.profile.name,
            "detected_by": result.detection.method,
            "description": result.detection.description,
        },
        "status": "PASSED" if result.passed else "FAILED",
        "summary": {
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "total_lines": source.line_count,
            "valid_lines": source.line_count - len(flagged),
            "flagged_lines": flagged,
            "total_tokens": result.token_count,
            "elapsed_ms": round(result.elapsed_ms, 2),
        },
        "errors_by_check": _check_totals(result),
        "tokens_by_category": [
            {
                "category": category.plural,
                "count": len(tokens),
                "items": dict(Counter(token.text for token in tokens)),
            }
            for category, tokens in group_by_category(result.lex.tokens).items()
        ],
        "diagnostics": [_diagnostic(d, result) for d in result.diagnostics],
        "lines": [
            {
                "number": line.number,
                "text": line.text,
                "label": line.label,
                "delimiters": line.delimiters,
                "status": _line_status(line.diagnostics, line.label),
                "codes": [d.code for d in line.diagnostics],
            }
            for line in result.lines
        ],
        "tokens": [
            {
                "text": token.text,
                "category": token.category.singular,
                "kind": token.kind.value,
                "line": token.line,
                "column": token.col,
                "end_line": token.end_line,
                "end_column": token.end_col,
                "issue": token.issue.value if token.issue else None,
            }
            for token in result.lex.tokens
        ],
    }


def to_json(result: AnalysisResult, indent: int | None = 2) -> str:
    return json.dumps(to_dict(result), indent=indent, ensure_ascii=False)


def _diagnostic(diagnostic: Diagnostic, result: AnalysisResult) -> dict:
    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity.value,
        "check": diagnostic.check.number,
        "check_title": diagnostic.check.title,
        "category": diagnostic.category,
        "message": diagnostic.message,
        "hint": diagnostic.hint,
        "line": diagnostic.line,
        "column": diagnostic.col,
        "code_line": result.source.line_text(diagnostic.line),
    }


def _check_totals(result: AnalysisResult) -> list[dict]:
    totals = {check: {"errors": 0, "warnings": 0} for check in Check}
    for diagnostic in result.diagnostics:
        totals[diagnostic.check]["errors" if diagnostic.is_error else "warnings"] += 1
    return [
        {"check": check.number, "title": check.title, **counts} for check, counts in totals.items()
    ]


def _line_status(diagnostics: list[Diagnostic], label: str | None) -> str:
    if any(d.is_error for d in diagnostics):
        return "error"
    if diagnostics:
        return "warning"
    return "blank" if label is None else "ok"
