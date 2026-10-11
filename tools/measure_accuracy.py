"""Measure how often SyntaxLens catches a known mistake.

    py tools/measure_accuracy.py            # the summary table
    py tools/measure_accuracy.py --misses   # also list every mistake that was missed

The valid programs in tests/data/ produce zero findings.  This script takes each
of them and plants ONE known mistake at a time (a missing ')', an unclosed
string, '+ /', a name starting with a digit, ...).  It then analyzes the broken
program and asks two questions:

    caught      is an error reported on the line where the mistake was planted?
    right check is that error reported by the check that owns this kind of mistake?

Every place where a mistake can be planted is tried, so a 150-line program gives
dozens of broken versions.  Nothing here changes the analyzer; it only measures it.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from syntaxlens.analyzer import analyze  # noqa: E402
from syntaxlens.detect import detect_language  # noqa: E402
from syntaxlens.diagnostics import Check  # noqa: E402
from syntaxlens.lexer import tokenize  # noqa: E402
from syntaxlens.source import from_text  # noqa: E402
from syntaxlens.tokens import Token, TokenKind  # noqa: E402

VALID = Path(__file__).resolve().parents[1] / "tests" / "data"

PY_HEADERS = {"if", "elif", "else", "while", "for", "def", "class", "try", "except", "finally", "with"}
C_TYPES = {"int", "double", "float", "char", "long", "bool", "boolean", "string", "String", "var", "auto"}
BINARY = {"+", "-", "==", "!=", "&&", "||", "and", "or"}
PLAIN_NUMBER = re.compile(r"\d+(\.\d+)?")

# A mutation gets one line (its text and tokens) and yields (new line text, the check that should
# catch it).  It may yield several variants, one per place on the line where the mistake fits.
Mutation = Iterator[tuple[str, Check]]


def drop_closing_paren(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'print(x)' -> 'print(x'"""
    depth = 0
    for token in tokens:
        depth += {"(": 1, ")": -1}.get(token.text, 0) if token.kind is TokenKind.DELIMITER else 0
        if depth < 0:
            return                                       # closes a '(' from an earlier line
    closers = [t for t in tokens if t.text == ")" and t.kind is TokenKind.DELIMITER]
    if depth == 0 and closers:
        last = closers[-1]
        yield text[:last.col - 1] + text[last.col:], Check.DELIMITERS


def unclose_string(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'"hello"' -> '"hello'"""
    for token in tokens:
        if token.kind is TokenKind.STRING and token.line == token.end_line and token.text.endswith('"') \
                and not token.text.endswith('"""') and not token.text.startswith(("R", "@", "$@")):
            yield text[:token.end_col - 2] + text[token.end_col - 1:], Check.LITERALS


def drop_terminator(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'x = 1;' -> 'x = 1'   and   'if x > 0:' -> 'if x > 0'"""
    last = tokens[-1]
    if python:
        if tokens[0].text in PY_HEADERS and last.text == ":" and len(tokens) > 2:
            yield text[:last.col - 1] + text[last.col:], Check.TERMINATORS
    elif last.text == ";" and tokens[0].text != "for" and len(tokens) > 1:
        yield text[:last.col - 1] + text[last.col:], Check.TERMINATORS


def double_operator(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'a + b' -> 'a + / b'"""
    for token in tokens[1:-1]:
        if token.text in BINARY and token.kind in (TokenKind.OPERATOR, TokenKind.KEYWORD):
            end = token.end_col - 1
            yield text[:end] + " /" + text[end:], Check.OPERATORS


def digit_name(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'total = 0' -> '2total = 0'   and   'int total = 0;' -> 'int 2total = 0;'"""
    if python:
        if len(tokens) > 2 and tokens[0].kind is TokenKind.IDENTIFIER and tokens[1].text == "=":
            name = tokens[0]
            yield text[:name.col - 1] + "2" + text[name.col - 1:], Check.IDENTIFIERS
    elif len(tokens) > 2 and tokens[0].text in C_TYPES and tokens[1].kind is TokenKind.IDENTIFIER \
            and tokens[2].text in ("=", ";"):
        name = tokens[1]
        yield text[:name.col - 1] + "2" + text[name.col - 1:], Check.IDENTIFIERS


def empty_condition(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'if x > 0:' -> 'if :'   and   'if (x > 0) {' -> 'if () {'"""
    first = tokens[0]
    if first.text not in ("if", "while", "elif"):
        return
    if python:
        if tokens[-1].text == ":" and len(tokens) > 2:
            yield text[:first.end_col - 1] + " " + text[tokens[-1].col - 1:], Check.CONTROL
    elif len(tokens) > 3 and tokens[1].text == "(":
        depth = 0
        for token in tokens[1:]:
            depth += {"(": 1, ")": -1}.get(token.text, 0)
            if depth == 0:
                yield text[:tokens[1].col] + text[token.col - 1:], Check.CONTROL
                return


def unexpected_indent(text: str, tokens: list[Token], python: bool, previous: str | None = None) -> Mutation:
    """Python: indent a line that follows an ordinary statement at the same level."""
    if python and previous is not None and tokens[0].text not in ("else", "elif", "except", "finally", "@") \
            and not previous.rstrip().endswith((":", ",", "(", "[", "{", "\\")):
        indent = len(text) - len(text.lstrip())
        if len(previous) - len(previous.lstrip()) == indent:
            yield text[:indent] + "    " + text[indent:], Check.BLOCKS


def malformed_number(text: str, tokens: list[Token], python: bool) -> Mutation:
    """'10' -> '10.1.2'"""
    for token in tokens:
        if token.kind is TokenKind.NUMBER and PLAIN_NUMBER.fullmatch(token.text):
            end = token.end_col - 1
            yield text[:end] + ".1.2" + text[end:], Check.LEXICAL


MUTATIONS = [drop_closing_paren, unclose_string, drop_terminator, double_operator,
             digit_name, empty_condition, unexpected_indent, malformed_number]


def broken_versions(path: Path) -> Iterator[tuple[int, str, Check]]:
    """Every (line, broken program, expected check) for one valid program."""
    text = path.read_text(encoding="utf-8")
    source = from_text(text, name=path.name)
    profile = detect_language(source).profile
    python = profile.family == "python"
    lines = text.split("\n")
    by_line: dict[int, list[Token]] = defaultdict(list)
    for token in tokenize(source, profile).tokens:
        if token.kind is not TokenKind.COMMENT:
            by_line[token.line].append(token)
    previous = None
    for number, line in enumerate(lines, start=1):
        tokens = by_line.get(number)
        if not tokens or tokens[0].line != tokens[-1].end_line:
            previous = None if not tokens else previous
            continue
        for mutation in MUTATIONS:
            extra = {"previous": previous} if mutation is unexpected_indent else {}
            for broken, check in mutation(line, tokens, python, **extra):
                yield number, "\n".join([*lines[:number - 1], broken, *lines[number:]]), check
        previous = line


def measure() -> tuple[dict[Check, list[int]], list[str]]:
    """Plant every mistake; return [tried, caught, right check] per check, and the misses."""
    totals: dict[Check, list[int]] = defaultdict(lambda: [0, 0, 0])
    misses: list[str] = []
    for path in sorted(VALID.glob("*_valid/*")):
        assert not analyze(from_text(path.read_text(encoding="utf-8"), name=path.name)).diagnostics, path
        for number, broken, check in broken_versions(path):
            result = analyze(from_text(broken, name=path.name))
            on_line = [d for d in result.errors if d.line == number]
            counts = totals[check]
            counts[0] += 1
            counts[1] += bool(on_line)
            counts[2] += any(d.check is check for d in on_line)
            if not on_line:
                misses.append(f"{path.parent.name}/{path.name}:{number}  [{check.title}]  "
                              f"{broken.split(chr(10))[number - 1].strip()}")
    return dict(totals), misses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--misses", action="store_true", help="list every planted mistake that was missed")
    args = parser.parse_args()

    totals, misses = measure()
    programs = sorted(VALID.glob("*_valid/*"))
    print(f"Planted one mistake at a time into {len(programs)} valid programs.\n")
    print(f"{'Check':<42}{'tried':>7}{'caught':>9}{'right check':>13}")
    for check in Check:
        if check in totals:
            tried, caught, right = totals[check]
            print(f"{check.number}. {check.title:<39}{tried:>7}{caught / tried:>9.1%}{right / tried:>13.1%}")
    tried, caught, right = (sum(t[i] for t in totals.values()) for i in range(3))
    print(f"{'All':<42}{tried:>7}{caught / tried:>9.1%}{right / tried:>13.1%}")
    if args.misses:
        print("\nMissed:" if misses else "\nNothing was missed.")
        for miss in misses:
            print("  " + miss)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
