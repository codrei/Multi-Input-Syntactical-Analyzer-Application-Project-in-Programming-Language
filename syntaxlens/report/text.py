"""Plain-text reports.

* :func:`format_report` - the SYNTACTICAL ANALYSIS REPORT, laid out exactly like
  the two example reports in the project specification.
* :func:`format_token_listing` - every token with its category (``syntaxlens tokens``).

The layout uses ASCII characters only, so it displays correctly in every
Windows console.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..analyzer import AnalysisResult
from ..detect import Detection
from ..diagnostics import Diagnostic
from ..lexer import LexResult
from ..source import Source
from ..tokens import Token, group_by_category

WIDTH = 60
HEAVY_RULE = "=" * WIDTH
LIGHT_RULE = "-" * WIDTH


def format_report(result: AnalysisResult) -> str:
    """The SYNTACTICAL ANALYSIS REPORT in the specification's format.

    Valid code gets a line-by-line breakdown (spec Example 1); code with errors
    gets the list of errors (spec Example 2).  Warnings, if any, follow.
    """
    source = result.source
    errors, warnings = result.errors, result.warnings
    lines = [HEAVY_RULE, _centered("SYNTACTICAL ANALYSIS REPORT"), HEAVY_RULE]
    if result.passed:
        extra = f", {_plural(len(warnings), 'Warning')}" if warnings else ""
        lines.append(f"Status: PASSED (0 Syntax Errors Found{extra})")
    else:
        lines.append(f"Status: FAILED ({_plural(len(errors), 'Syntax Error')} Detected)")
    lines += [
        f"Total Lines Analyzed: {source.line_count}",
        f"Target Syntax Rule: {result.detection.description}",
        "",
    ]

    if result.passed:
        lines += ["LINE BREAKDOWN & SYNTAX CHECK:", LIGHT_RULE]
        for line in result.lines:
            if line.label is None:
                continue                                   # blank line
            verdict = "WARNING" if line.diagnostics else "OK"
            lines += [
                f"Line {line.number}: [{line.text.strip()}]",
                f"  - Syntax Check: {line.label} -> {verdict}",
                f"  - Delimiters: {line.delimiters}",
                "",
            ]
        lines += _warning_section(warnings, result)
        lines += [
            LIGHT_RULE,
            "SUMMARY:",
            f"  - Total Tokens Parsed: {result.token_count}",
            "  - Delimiter Balance: OK",
            "  - Syntax Validation: SUCCESSFUL",
        ]
    else:
        lines += ["SYNTAX ERROR DETAILS:", LIGHT_RULE]
        for number, error in enumerate(errors, start=1):
            lines += _entry("ERROR", number, error, result)
        lines += _warning_section(warnings, result)
        flagged = result.flagged_lines
        which = ", ".join(str(n) for n in flagged)
        lines += [
            LIGHT_RULE,
            "SUMMARY:",
            f"  - Total Lines Checked: {source.line_count}",
            f"  - Valid Lines: {source.line_count - len(flagged)}",
            f"  - Flagged Lines: {len(flagged)} ({'Lines' if len(flagged) > 1 else 'Line'} {which})",
            "  - Action Required: Correct highlighted syntax errors above.",
        ]
    lines.append(HEAVY_RULE)
    return "\n".join(lines)


def _entry(kind: str, number: int, diagnostic: Diagnostic, result: AnalysisResult) -> list[str]:
    code_line = result.source.line_text(diagnostic.line).strip()
    return [
        f"[{kind} {number}] Line {diagnostic.line}: {code_line}",
        f"  - Category: {diagnostic.category}",
        f"  - Details: {diagnostic.message}",
        "",
    ]


def _warning_section(warnings: list[Diagnostic], result: AnalysisResult) -> list[str]:
    if not warnings:
        return []
    lines = [LIGHT_RULE, "WARNINGS (valid code that is probably a mistake):", LIGHT_RULE]
    for number, warning in enumerate(warnings, start=1):
        lines += _entry("WARNING", number, warning, result)
    return lines


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def format_token_listing(source: Source, detection: Detection, result: LexResult) -> str:
    """Every token with its position and category, then totals per category."""
    lines = [
        HEAVY_RULE,
        _centered("LEXICAL ANALYSIS: TOKEN LIST"),
        HEAVY_RULE,
        f"Source: {source.name}",
        f"Language: {detection.description}",
        f"Total Lines: {source.line_count}",
        "",
        f"{'#':>4}  {'LINE:COL':<8}  {'CATEGORY':<20}  TOKEN",
        LIGHT_RULE,
    ]
    for number, token in enumerate(result.tokens, start=1):
        position = f"{token.line}:{token.col}"
        row = f"{number:>4}  {position:<8}  {token.category.singular:<20}  {_printable(token.text)}"
        if token.issue:
            row += f"   <-- {token.issue.value}"
        lines.append(row)

    lines += [LIGHT_RULE, "TOKEN SUMMARY BY CATEGORY:"]
    for category, tokens in group_by_category(result.tokens).items():
        lines.append(f"  {_dotted(category.plural)} {len(tokens):>3}  {_distinct(tokens)}".rstrip())
    lines.append(f"  {_dotted('Total Tokens Parsed')} {len(result.tokens):>3}")

    flagged = sum(1 for token in result.tokens if token.issue)
    if flagged or result.odd_spaces:
        lines.append("")
        if flagged:
            lines.append(f"NOTE: {flagged} token(s) have a lexical problem (marked with <--).")
        for line, col, char in result.odd_spaces:
            lines.append(
                f"NOTE: invisible look-alike space U+{ord(char):04X} at line {line}, column {col}."
            )
    lines.append(HEAVY_RULE)
    return "\n".join(lines)


def _centered(title: str) -> str:
    return title.center(WIDTH).rstrip()


def _dotted(label: str, width: int = 24) -> str:
    """'Keywords' -> 'Keywords ................' so the counts line up."""
    return f"{label} ".ljust(width, ".")


def _printable(text: str, limit: int = 32) -> str:
    """Show token text on one line: escape line breaks and tabs, shorten long text."""
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _distinct(tokens: Iterable[Token], limit: int = 8) -> str:
    """The distinct token texts in order of appearance, e.g. 'x (x2), print'."""
    counts: dict[str, int] = {}
    for token in tokens:
        text = _printable(token.text, 20)
        counts[text] = counts.get(text, 0) + 1
    shown = [text if count == 1 else f"{text} (x{count})" for text, count in counts.items()]
    if len(shown) > limit:
        shown = shown[:limit] + [f"... +{len(shown) - limit} more"]
    return ", ".join(shown)
