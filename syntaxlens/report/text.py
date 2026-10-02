"""Plain-text reports.

Phase 1 provides the token listing used by ``syntaxlens tokens``.  The full
SYNTACTICAL ANALYSIS REPORT in the spec's format is added in Phase 4.

The layout uses ASCII characters only, so it displays correctly in every
Windows console.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..detect import Detection
from ..lexer import LexResult
from ..source import Source
from ..tokens import Token, group_by_category

WIDTH = 60
HEAVY_RULE = "=" * WIDTH
LIGHT_RULE = "-" * WIDTH


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
