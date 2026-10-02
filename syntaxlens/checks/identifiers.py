"""Check 6: identifier naming rules.

A name (variable, function, class) must start with a letter or '_' (Java also
allows '$'), may continue with letters, digits and '_', and must not be a
reserved keyword.  The lexer's regular expression already enforces the
character rules: a "name" such as ``2total`` is marked as starting with a digit.
This check reports those marks, and also catches names broken by a '-' or a
space (``my-var = 3``, ``int my var;``) and keywords used as names
(``class = 5``, ``int for = 3;``).
"""

from __future__ import annotations

from ..diagnostics import Check, Diagnostic, at
from ..structure import ASSIGNMENT_OPS, Statement, find_top, is_delim, skip_type, split_top
from ..tokens import Issue, Token, TokenKind
from . import Context

CATEGORY = "Invalid Identifier"


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for token in context.lex.tokens:
        if token.issue is Issue.NAME_STARTS_WITH_DIGIT:
            digits = len(token.text) - len(token.text.lstrip("0123456789"))
            suggestion = token.text[digits:] + token.text[:digits]
            diagnostics.append(at(
                token, Check.IDENTIFIERS, "E601", CATEGORY,
                f"Invalid identifier '{token.text}': names cannot start with a digit.",
                hint=f"Start the name with a letter or '_', e.g. '{suggestion}'.",
                statement=context.statement_index(token),
            ))
    for statement in context.statements:
        for target in _names_declared(statement, context.python):
            diagnostics += _check_name(target, statement)
        if not context.python:
            missing = _missing_name(statement)
            if missing:
                diagnostics.append(missing)
    return diagnostics


def broken_name(tokens: list[Token]) -> str | None:
    """'my_var' if ``tokens`` look like one name broken by '-' or spaces, else None.

    my-var  ->  three tokens (my, -, var) written with no spaces between them
    my var  ->  two names with only a space between them
    """
    if len(tokens) < 2 or tokens[0].kind is not TokenKind.IDENTIFIER:
        return None
    words = [token for token in tokens if token.kind in (TokenKind.IDENTIFIER, TokenKind.NUMBER)]
    if all(token.kind is TokenKind.IDENTIFIER for token in tokens):
        return "_".join(token.text for token in tokens)
    hyphenated = all(
        token.text == "-" if position % 2 else token.kind in (TokenKind.IDENTIFIER, TokenKind.NUMBER)
        for position, token in enumerate(tokens)
    ) and len(tokens) % 2 == 1
    touching = all(
        left.line == right.line and left.end_col == right.col
        for left, right in zip(tokens, tokens[1:], strict=False)
    )
    if hyphenated and touching:
        return "_".join(token.text for token in words)
    return None


def _check_name(target: list[Token], statement: Statement) -> list[Diagnostic]:
    if not target:
        return []
    first = target[0]
    fixed = broken_name(target)
    if fixed:
        written = "".join(
            token.text if position == 0 or target[position - 1].end_col == token.col
            else " " + token.text for position, token in enumerate(target)
        )
        reason = "'-'" if any(token.text == "-" for token in target) else "spaces"
        return [at(first, Check.IDENTIFIERS, "E602", CATEGORY,
                   f"Invalid identifier '{written}': names cannot contain {reason}.",
                   hint=f"Use an underscore instead: {fixed}", statement=statement.index)]
    if len(target) == 1 and first.kind is TokenKind.KEYWORD and first.text not in ("this", "super"):
        return [at(first, Check.IDENTIFIERS, "E603", "Reserved Word Used as Name",
                   f"'{first.text}' is a reserved keyword and cannot be used as a name.",
                   hint=f"Choose another name, e.g. '{first.text}_value'.",
                   statement=statement.index)]
    return []


def _names_declared(statement: Statement, python: bool) -> list[list[Token]]:
    """The token groups that a statement uses as new names."""
    code = statement.code
    if code and code[-1].text == ";":
        code = code[:-1]
    if not code:
        return []
    if python:
        return _python_names(statement, code)
    return _c_names(statement, code)


def _python_names(statement: Statement, code: list[Token]) -> list[list[Token]]:
    if statement.header and statement.keyword in ("def", "class"):
        body = code[2:] if code[0].text == "async" else code[1:]
        return [body[:1]] if body and body[0].kind is TokenKind.KEYWORD else []
    if statement.kind not in ("assignment", "declaration"):
        return []
    names = []
    for index, token in enumerate(code):
        if token.kind is TokenKind.OPERATOR and token.text in ASSIGNMENT_OPS:
            target = code[:index]
            colon = find_top(target, ":")
            target = target[:colon] if colon is not None else target
            names += [part for part in split_top(target, ",") if part]
            break
    else:
        colon = find_top(code, ":")
        if colon is not None:
            names.append(code[:colon])
    return names


def _c_names(statement: Statement, code: list[Token]) -> list[list[Token]]:
    if statement.kind not in ("declaration", "method"):
        return []
    after_type = _after_type(code)
    if after_type is None or after_type >= len(code) or code[after_type].text in ASSIGNMENT_OPS:
        return []                                # no name at all: see _missing_name
    if statement.kind == "method":
        return [code[after_type: after_type + 1]]
    names = []
    for declarator in split_top(code[after_type:], ","):
        position = find_top(declarator, "=")
        name = declarator[:position] if position is not None else declarator
        while len(name) >= 2 and is_delim(name[-1], "]") and is_delim(name[-2], "["):
            name = name[:-2]                     # int scores[] (C-style array syntax)
        names.append(name)
    return names


def _missing_name(statement: Statement) -> Diagnostic | None:
    """'int = 5;' declares a variable without a name."""
    code = statement.code
    if statement.kind != "declaration" or not code:
        return None
    after_type = _after_type(code)
    if after_type is not None and after_type < len(code) and code[after_type].text in ASSIGNMENT_OPS:
        type_token = code[after_type - 1]
        return at(code[after_type], Check.IDENTIFIERS, "E604", CATEGORY,
                  f"Missing variable name after the type '{type_token.text}'.",
                  hint=f"Write a name between the type and '=', e.g. {type_token.text} total = ...",
                  statement=statement.index)
    return None


_MODIFIERS = frozenset(
    "final static public private protected abstract transient volatile synchronized native "
    "default".split()
)


def _after_type(code: list[Token]) -> int | None:
    """Index just after the declared type, skipping modifiers and annotations."""
    index = 0
    while index < len(code) and (code[index].text in _MODIFIERS or is_delim(code[index], "@")):
        index += 2 if is_delim(code[index], "@") else 1
    return skip_type(code, index)
