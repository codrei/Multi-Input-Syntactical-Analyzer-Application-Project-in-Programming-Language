"""Check 1: delimiter and bracket matching.

The data structure is a **stack** (last in, first out):

* An opening bracket ``(``, ``[`` or ``{`` is pushed onto the stack.
* A closing bracket must match the bracket on top of the stack, which is the
  most recently opened one.  If it does, the top is popped.  This is what
  makes nesting work: in ``f(a[0])`` the ``]`` closes the ``[`` before the
  ``)`` closes the ``(``.
* Anything still on the stack when the statement ends was never closed.

Parentheses and square brackets must close inside their own statement.  In
C-family code, braces ``{ }`` that delimit blocks are matched across the whole
file instead.  Brackets inside strings and comments are never seen, because
the lexer turned those into single tokens.
"""

from __future__ import annotations

from ..diagnostics import Check, Diagnostic, at
from ..structure import CLOSERS, OPENERS, Statement, is_delim
from ..tokens import Token
from . import Context

NAMES = {"(": "parenthesis", "[": "square bracket", "{": "curly brace",
         ")": "parenthesis", "]": "square bracket", "}": "curly brace"}
CATEGORY = "Delimiter / Bracket Mismatch"

_ENDINGS = {";": "before ';'", "{": "before '{'", ":": "before ':'"}


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for statement in context.statements:
        diagnostics += [problem for problem in scan(statement, context.python)]
    if not context.python:
        diagnostics += _check_blocks(context.statements)
    return diagnostics


def scan(statement: Statement, python: bool) -> list[Diagnostic]:
    """Match the brackets inside one statement with a stack."""
    problems: list[Diagnostic] = []
    stack: list[Token] = []
    tokens = statement.tokens
    if not python and statement.kind == "block_end":
        return problems
    if not python and statement.ended_by == "{":
        tokens = tokens[:-1]               # the block's '{' is matched across the file
    if python and statement.header and not statement.has_colon and is_delim(tokens[-1], "{"):
        tokens = tokens[:-1]               # "if x {": reported as a missing ':' instead

    def problem(token: Token, code: str, message: str, hint: str) -> None:
        problems.append(at(token, Check.DELIMITERS, code, CATEGORY, message,
                           hint=hint, statement=statement.index))

    for token in tokens:
        if is_delim(token, *OPENERS):
            stack.append(token)
        elif is_delim(token, *CLOSERS):
            wanted = CLOSERS[token.text]
            if stack and stack[-1].text == wanted:
                stack.pop()
            elif any(opener.text == wanted for opener in stack):
                # Something opened after the matching bracket was never closed.
                while stack[-1].text != wanted:
                    opener = stack.pop()
                    problem(opener, "E101",
                            f"Unclosed {NAMES[opener.text]} '{opener.text}'. "
                            f"Expected '{OPENERS[opener.text]}' before '{token.text}'.",
                            f"Add '{OPENERS[opener.text]}' before the '{token.text}'.")
                stack.pop()
            elif stack:
                opener = stack.pop()
                problem(token, "E103",
                        f"Mismatched closing {NAMES[token.text]} '{token.text}': expected "
                        f"'{OPENERS[opener.text]}' to close the '{opener.text}' "
                        f"at line {opener.line}, column {opener.col}.",
                        f"Change '{token.text}' to '{OPENERS[opener.text]}'.")
            else:
                problem(token, "E102",
                        f"Unexpected closing {NAMES[token.text]} '{token.text}' "
                        f"with no matching '{wanted}'.",
                        f"Remove the '{token.text}', or add the missing '{wanted}' before it.")
    ending = _ENDINGS.get(statement.ended_by, "before line end")
    for opener in stack:
        closer = OPENERS[opener.text]
        problem(opener, "E101",
                f"Unclosed {NAMES[opener.text]} '{opener.text}'. Expected '{closer}' {ending}.",
                f"Add the missing '{closer}'.")
    return problems


def _check_blocks(statements: list[Statement]) -> list[Diagnostic]:
    """Match block braces across the whole file (C family)."""
    problems: list[Diagnostic] = []
    open_blocks: list[Statement] = []
    for statement in statements:
        if statement.ended_by == "{":
            open_blocks.append(statement)
        elif statement.kind == "block_end":
            if open_blocks:
                open_blocks.pop()
            else:
                problems.append(at(statement.first, Check.DELIMITERS, "E102", CATEGORY,
                                   "Unexpected closing curly brace '}' with no matching '{'.",
                                   hint="Remove the extra '}'.", statement=statement.index))
    for header in open_blocks:
        brace = header.last
        problems.append(at(brace, Check.DELIMITERS, "E101", CATEGORY,
                           "Unclosed curly brace '{'. Expected '}' before the end of the input.",
                           hint=f"Add a '}}' to close the block opened on line {brace.line}.",
                           statement=header.index))
    return problems
