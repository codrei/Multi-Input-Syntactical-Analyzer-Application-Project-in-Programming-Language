"""The analysis pipeline: from input text to a finished result.

    source  ->  detect language  ->  lexer  ->  statements  ->  8 checks
            ->  cascade filter   ->  line breakdown  ->  AnalysisResult

The **cascade filter** is what makes the spec's Example 2 report exactly three
errors.  One mistake often causes several symptoms in the same statement:

    if (x > 5                  unclosed '('  ...and so the ':' looks missing too
    print("Value is valid)     unclosed '"'  ...which swallowed the ')' as well

Only the root cause is kept.  Within one statement:

* an error found by the lexer (unclosed string, illegal character) hides the
  bracket, terminator, header and operator errors in that statement;
* a bracket error hides the terminator, header and operator errors in it.

Naming errors and indentation errors are always kept: they are independent.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from .checks import Context, run_all
from .checks.delimiters import scan
from .detect import Detection, detect_language
from .diagnostics import Check, Diagnostic, Severity
from .lexer import LexResult, tokenize
from .source import Source, from_text
from .structure import Statement, build_statements
from .tokens import Token, TokenKind

_LEXICAL_ROOTS = {Check.LITERALS, Check.LEXICAL}
_HIDDEN_BY_LEXICAL = {Check.DELIMITERS, Check.TERMINATORS, Check.CONTROL, Check.OPERATORS}
_HIDDEN_BY_DELIMITERS = {Check.TERMINATORS, Check.CONTROL, Check.OPERATORS}


@dataclass
class LineReport:
    """What the report says about one physical line."""

    number: int
    text: str
    label: str | None            # e.g. "Variable Assignment"; None for a blank line
    delimiters: str              # e.g. "Parentheses () Balanced | Colon ':' Present"
    diagnostics: list[Diagnostic]

    @property
    def has_error(self) -> bool:
        return any(d.is_error for d in self.diagnostics)


@dataclass
class AnalysisResult:
    """Everything one analysis produced."""

    source: Source
    detection: Detection
    lex: LexResult
    statements: list[Statement]
    diagnostics: list[Diagnostic]
    lines: list[LineReport]
    elapsed_ms: float

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity is Severity.WARNING]

    @property
    def passed(self) -> bool:
        return not self.errors

    @property
    def token_count(self) -> int:
        return len(self.lex.tokens)

    @property
    def flagged_lines(self) -> list[int]:
        return sorted({d.line for d in self.errors})

    def errors_by_check(self) -> dict[Check, int]:
        counts = {check: 0 for check in Check}
        for diagnostic in self.errors:
            counts[diagnostic.check] += 1
        return counts


def analyze(source: Source, language: str = "auto") -> AnalysisResult:
    """Run the whole pipeline on ``source``."""
    started = time.perf_counter()
    detection = detect_language(source, language)
    lex = tokenize(source, detection.profile)
    statements = build_statements(source, lex)
    context = Context(source, lex, statements)
    diagnostics = filter_cascades(run_all(context))
    diagnostics.sort(key=lambda d: (d.line, d.col, d.check.number))
    lines = _line_reports(source, lex, statements, diagnostics)
    elapsed = (time.perf_counter() - started) * 1000
    return AnalysisResult(source, detection, lex, statements, diagnostics, lines, elapsed)


def analyze_text(text: str, language: str = "auto", name: str = "<input>") -> AnalysisResult:
    """Convenience wrapper: analyze a string of code."""
    return analyze(from_text(text, name=name), language)


def filter_cascades(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Keep root causes; drop the follow-on errors they cause in the same statement."""
    by_statement: dict[int | None, list[Diagnostic]] = defaultdict(list)
    for diagnostic in diagnostics:
        by_statement[diagnostic.statement].append(diagnostic)
    kept: list[Diagnostic] = []
    seen: set[tuple[int, int, str]] = set()
    # A comment or string that runs to the end of the input swallowed everything after
    # it, so blocks opened earlier look unclosed.  Only the comment/string is reported.
    runs_to_end = any(d.code == "E803" or (d.code == "E201" and "triple" in d.message)
                      for d in diagnostics)
    for statement, group in by_statement.items():
        lexical_root = statement is not None and any(
            d.check in _LEXICAL_ROOTS and d.is_error for d in group
        )
        bracket_root = statement is not None and any(d.check is Check.DELIMITERS for d in group)
        for diagnostic in group:
            if runs_to_end and diagnostic.code in ("E101", "E702") and \
                    diagnostic.message.endswith(("end of the input.", "the input ended.")):
                continue
            if lexical_root and diagnostic.check in _HIDDEN_BY_LEXICAL:
                continue
            if bracket_root and diagnostic.check in _HIDDEN_BY_DELIMITERS:
                continue
            key = (diagnostic.line, diagnostic.col, diagnostic.code)
            if key not in seen:
                seen.add(key)
                kept.append(diagnostic)
    return kept


# ------------------------------------------------------------ line breakdown

def _line_reports(source: Source, lex: LexResult, statements: list[Statement],
                  diagnostics: list[Diagnostic]) -> list[LineReport]:
    python = lex.profile.family == "python"
    starting: dict[int, list[Statement]] = defaultdict(list)
    continued: dict[int, Statement] = {}
    for statement in statements:
        starting[statement.first_line].append(statement)
        for line in range(statement.first_line + 1, statement.last_line + 1):
            continued.setdefault(line, statement)
    comment_lines = {token.line for token in lex.tokens if token.kind is TokenKind.COMMENT}
    by_line: dict[int, list[Diagnostic]] = defaultdict(list)
    for diagnostic in diagnostics:
        by_line[diagnostic.line].append(diagnostic)

    reports = []
    for number, text in enumerate(source.lines, start=1):
        if starting[number]:
            group = starting[number]
            labels = list(dict.fromkeys(statement.label for statement in group))
            label = " + ".join(labels)
            notes = " | ".join(
                note for statement in group for note in _delimiter_notes(statement, statements, python)
            ) or "Balanced"
        elif number in continued:
            label = f"Continuation of line {continued[number].first_line}"
            notes = f"(checked with line {continued[number].first_line})"
        elif number in comment_lines:
            label, notes = "Comment (ignored by the checks)", "None"
        else:
            label, notes = None, ""
        reports.append(LineReport(number, text, label, notes, by_line[number]))
    return reports


_BRACKET_NAMES = {"(": "Parentheses ()", "[": "Square Brackets []", "{": "Curly Braces {}"}


def _delimiter_notes(statement: Statement, statements: list[Statement], python: bool) -> list[str]:
    """Short facts about a statement's delimiters, for the line breakdown."""
    notes: list[str] = []
    if statement.kind == "block_end":
        if statement.opener is not None:
            notes.append(f"Curly Brace '}}' Closes the Block from Line "
                         f"{statements[statement.opener].first_line}")
        else:
            notes.append("Curly Brace '}' Has No Matching '{'")
        return notes

    tokens = statement.tokens[:-1] if (not python and statement.ended_by == "{") else statement.tokens
    unbalanced = set()
    for problem in scan(statement, python):
        char = _char_at(statement.tokens, problem.line, problem.col)
        if char:
            unbalanced.add({")": "(", "]": "[", "}": "{"}.get(char, char))
    for opener, name in _BRACKET_NAMES.items():
        if any(token.kind is TokenKind.DELIMITER and token.text in (opener, _close(opener))
               for token in tokens):
            notes.append(f"{name} {'Unbalanced' if opener in unbalanced else 'Balanced'}")

    strings = [token for token in tokens if token.kind in (TokenKind.STRING, TokenKind.CHAR)]
    for quote, name in (('"', 'String Quotes ""'), ("'", "String Quotes ''")):
        matching = [token for token in strings
                    if token.text.lstrip("rRbBuUfFtTL@$")[:1] == quote and token.kind is TokenKind.STRING]
        if matching:
            closed = all(token.issue is None for token in matching)
            notes.append(f"{name} {'Balanced' if closed else 'Unclosed'}")
    chars = [token for token in strings if token.kind is TokenKind.CHAR]
    if chars:
        notes.append(f"Char Quotes '' {'Balanced' if all(t.issue is None for t in chars) else 'Unclosed'}")

    if python and statement.header:
        notes.append(f"Colon ':' {'Present' if statement.has_colon else 'Missing'}")
    elif not python:
        if statement.ended_by == "{":
            closer = statement.closer_line
            notes.append(f"Curly Brace '{{' Opens a Block (closed on Line {closer})" if closer
                         else "Curly Brace '{' Opens a Block (never closed)")
        elif statement.ended_by == ";":
            notes.append("Semicolon ';' Present")
        elif statement.missing_terminator:
            notes.append("Semicolon ';' Missing")
    return notes


def _close(opener: str) -> str:
    return {"(": ")", "[": "]", "{": "}"}[opener]


def _char_at(tokens: list[Token], line: int, col: int) -> str | None:
    for token in tokens:
        if token.line == line and token.col == col:
            return token.text
    return None
