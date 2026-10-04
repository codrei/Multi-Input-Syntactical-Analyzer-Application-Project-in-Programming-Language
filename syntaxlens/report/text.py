"""Plain-text reports.

:func:`format_report` prints the SYNTACTICAL ANALYSIS REPORT in one of two styles:

* ``"classic"`` - exactly the layout and wording of the two example reports in
  the project specification.
* ``"detailed"`` (the default on the command line) - the same report, plus:

  - for each error: its code, the check that found it, a pointer to the exact
    column, and a suggested fix;
  - a line-by-line breakdown, also when the code has errors;
  - totals for each of the 8 syntax checks and each of the 8 token categories,
    with the tokens found in each ("detailed lists of identified items and
    summary totals for each category", as the specification requires).

:func:`format_token_listing` lists every token with its category (``syntaxlens tokens``).

The layout uses ASCII characters only, so it displays correctly in every
Windows console.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..analyzer import AnalysisResult
from ..detect import Detection
from ..diagnostics import Check, Diagnostic
from ..lexer import LexResult
from ..source import Source
from ..tokens import Token, group_by_category

WIDTH = 60
HEAVY_RULE = "=" * WIDTH
LIGHT_RULE = "-" * WIDTH
STYLES = ("detailed", "classic")

#: How many characters of a code line the column pointer shows.
_SNIPPET_WIDTH = 72


def format_report(result: AnalysisResult, style: str = "classic") -> str:
    """The SYNTACTICAL ANALYSIS REPORT.

    Valid code gets a line-by-line breakdown (spec Example 1); code with errors
    gets the list of errors (spec Example 2).  See the module docstring for
    what the "detailed" style adds.
    """
    if style not in STYLES:
        raise ValueError(f"Unknown report style '{style}'. Choose one of: {', '.join(STYLES)}.")
    detailed = style == "detailed"
    source = result.source
    errors, warnings = result.errors, result.warnings
    numbers = _numbering(errors, warnings)

    lines = [HEAVY_RULE, _centered("SYNTACTICAL ANALYSIS REPORT"), HEAVY_RULE]
    if result.passed:
        extra = f", {_plural(len(warnings), 'Warning')}" if warnings else ""
        lines.append(f"Status: PASSED (0 Syntax Errors Found{extra})")
    else:
        lines.append(f"Status: FAILED ({_plural(len(errors), 'Syntax Error')} Detected)")
    lines += [
        f"Total Lines Analyzed: {source.line_count}",
        f"Target Syntax Rule: {result.detection.description}",
    ]
    if detailed:
        lines.append(f"Source: {source.name}")
    lines.append("")

    if result.passed:
        lines += _breakdown(result, numbers)
        lines += _warning_section(warnings, result, detailed)
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
            lines += _entry("ERROR", number, error, result, detailed)
        lines += _warning_section(warnings, result, detailed)
        if detailed:
            lines += [LIGHT_RULE] + _breakdown(result, numbers)
        flagged = result.flagged_lines
        which = ", ".join(str(n) for n in flagged)
        lines += [
            LIGHT_RULE,
            "SUMMARY:",
            f"  - Total Lines Checked: {source.line_count}",
            f"  - Valid Lines: {source.line_count - len(flagged)}",
            f"  - Flagged Lines: {len(flagged)} ({'Lines' if len(flagged) > 1 else 'Line'} {which})",
        ]
        if detailed:
            lines.append(f"  - Total Tokens Parsed: {result.token_count}")
        lines.append("  - Action Required: Correct highlighted syntax errors above.")
    if detailed:
        lines += [""] + _check_totals(result) + [""] + _token_totals(result.lex.tokens)
    lines.append(HEAVY_RULE)
    return "\n".join(lines)


# ------------------------------------------------------------------ sections

def _breakdown(result: AnalysisResult, numbers: dict[int, str]) -> list[str]:
    """LINE BREAKDOWN & SYNTAX CHECK: one entry per non-blank line."""
    lines = ["LINE BREAKDOWN & SYNTAX CHECK:", LIGHT_RULE]
    for line in result.lines:
        if line.label is None:
            continue                                     # blank line
        references = [numbers[id(d)] for d in line.diagnostics if id(d) in numbers]
        if any(d.is_error for d in line.diagnostics):
            verdict = f"ERROR (see {', '.join(references)})"
        elif line.diagnostics:
            verdict = f"WARNING (see {', '.join(references)})"
        else:
            verdict = "OK"
        lines += [
            f"Line {line.number}: [{line.text.strip()}]",
            f"  - Syntax Check: {line.label} -> {verdict}",
            f"  - Delimiters: {line.delimiters}",
            "",
        ]
    return lines


def _entry(kind: str, number: int, diagnostic: Diagnostic, result: AnalysisResult,
           detailed: bool) -> list[str]:
    """One [ERROR n] or [WARNING n] entry."""
    code_line = result.source.line_text(diagnostic.line).strip()
    lines = [
        f"[{kind} {number}] Line {diagnostic.line}: {code_line}",
        f"  - Category: {diagnostic.category}",
        f"  - Details: {diagnostic.message}",
    ]
    if detailed:
        check = diagnostic.check
        lines.append(f"  - Location: line {diagnostic.line}, column {diagnostic.col} "
                     f"(check {check.number}: {check.title}, code {diagnostic.code})")
        lines += pointer(result.source, diagnostic.line, diagnostic.col)
        if diagnostic.hint:
            lines.append(f"  - Fix: {diagnostic.hint}")
    lines.append("")
    return lines


def _warning_section(warnings: list[Diagnostic], result: AnalysisResult, detailed: bool) -> list[str]:
    if not warnings:
        return []
    lines = [LIGHT_RULE, "WARNINGS (valid code that is probably a mistake):", LIGHT_RULE]
    for number, warning in enumerate(warnings, start=1):
        lines += _entry("WARNING", number, warning, result, detailed)
    return lines


def _check_totals(result: AnalysisResult) -> list[str]:
    """ERRORS BY CATEGORY: how many problems each of the 8 checks found."""
    errors = {check: 0 for check in Check}
    warnings = {check: 0 for check in Check}
    for diagnostic in result.diagnostics:
        (errors if diagnostic.is_error else warnings)[diagnostic.check] += 1
    lines = ["ERRORS BY CATEGORY (the 8 syntax checks):"]
    for check in Check:
        count = f"{errors[check]:>3}"
        if warnings[check]:
            count += f"  (+{_plural(warnings[check], 'warning')})"
        lines.append(f"  {_dotted(f'{check.number}. {check.title}', 46)} {count}")
    lines.append(f"  {_dotted('Total', 46)} {len(result.errors):>3}  "
                 f"({_plural(len(result.warnings), 'warning')})")
    return lines


def _token_totals(tokens: list[Token]) -> list[str]:
    """TOKENS BY CATEGORY: the 8 token categories, with the tokens found in each."""
    lines = ["TOKENS BY CATEGORY (the 8 token categories):"]
    for category, members in group_by_category(tokens).items():
        lines.append(f"  {_dotted(category.plural)} {len(members):>3}  {_distinct(members)}".rstrip())
    lines.append(f"  {_dotted('Total Tokens Parsed')} {len(tokens):>3}")
    return lines


def pointer(source: Source, line: int, col: int) -> list[str]:
    """Show the code line with a caret under the column, like a compiler does::

            4 | y = 20 + * 5
              |          ^

    Tabs are expanded so the caret lines up, and long lines are cut to a window
    around the column.
    """
    raw = source.line_text(line)
    visual = 0
    for char in raw[: max(col - 1, 0)]:
        visual += 4 - visual % 4 if char == "\t" else 1
    text = raw.expandtabs(4)
    if len(text) > _SNIPPET_WIDTH:
        start = max(0, min(visual - _SNIPPET_WIDTH // 2, len(text) - _SNIPPET_WIDTH))
        text = ("..." if start else "") + text[start: start + _SNIPPET_WIDTH] + (
            "..." if start + _SNIPPET_WIDTH < len(text) else ""
        )
        visual = visual - start + (3 if start else 0)
    gutter = str(line)
    return [
        f"      {gutter} | {text}".rstrip(),
        f"      {' ' * len(gutter)} | {' ' * visual}^",
    ]


def _numbering(errors: list[Diagnostic], warnings: list[Diagnostic]) -> dict[int, str]:
    """'ERROR 1', 'WARNING 2', ... for each diagnostic, keyed by identity."""
    numbers = {id(d): f"ERROR {n}" for n, d in enumerate(errors, start=1)}
    numbers.update({id(d): f"WARNING {n}" for n, d in enumerate(warnings, start=1)})
    return numbers


# ------------------------------------------------------------- token listing

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


# ------------------------------------------------------------------ helpers

def _centered(title: str) -> str:
    return title.center(WIDTH).rstrip()


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


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
