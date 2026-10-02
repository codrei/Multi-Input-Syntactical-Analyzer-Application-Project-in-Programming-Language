"""Check 7: indentation and block structure.

Python marks blocks by indentation.  As in CPython, a **stack of indentation
levels** is kept:

* After a header ending in ':', the next line must be indented further.  Its
  width is pushed as a new level.
* A line indented more without such a header is an "unexpected indent".
* A line indented less pops levels until one matches.  If none matches
  exactly, the indentation is inconsistent ("unindent does not match").
* A tab moves to the next multiple of 8.  Widths are also compared with a
  tab counted as 1; if the two comparisons disagree, tabs and spaces were
  mixed ambiguously.

The same pass checks that blocks pair up correctly: ``elif``/``else`` need an
``if`` before them, ``break``/``continue`` must be inside a loop, ``return``
inside a function, and a ``case`` inside ``match`` or ``switch``.

Recovery: a header with a syntax error (for example ``if (x > 5`` missing its
':') still opens a block, so the indented line after it is not reported as
well.  Only the original mistake is reported.
"""

from __future__ import annotations

from ..diagnostics import Check, Diagnostic, at
from ..structure import Statement
from . import Context

INDENT = "Indentation Error"
BLOCK = "Block Structure Error"

_PY_FOLLOWS = {
    "elif": ({"if", "elif"}, "'elif' without a matching 'if' before it."),
    "else": ({"if", "elif", "for", "while", "try", "except"},
             "'else' without a matching 'if' (or loop / try) before it."),
    "except": ({"try", "except"}, "'except' without a matching 'try' before it."),
    "finally": ({"try", "except", "else"}, "'finally' without a matching 'try' before it."),
}
_LOOPS = {"for", "while", "do"}


def check(context: Context) -> list[Diagnostic]:
    if context.python:
        return _python(context.statements)
    return _c_family(context.statements)


# ----------------------------------------------------------------- Python

def _python(statements: list[Statement]) -> list[Diagnostic]:
    problems: list[Diagnostic] = []
    levels = [(0, 0)]              # stack of indentation widths: (tab = 8, tab = 1)
    owners: list[str | None] = [None]   # header keyword that opened each level
    last_at: dict[int, str] = {}   # depth -> keyword of the last statement at that depth
    waiting: Statement | None = None    # header still waiting for its indented block
    inline_owner: str | None = None

    def report(statement: Statement, code: str, category: str, message: str, hint: str):
        problems.append(at(statement.first, Check.BLOCKS, code, category, message,
                           hint=hint, statement=statement.index))

    for statement in statements:
        if statement.inline:
            _python_pairing(statement, owners + [inline_owner], report)
            continue
        inline_owner = None
        width, alt = statement.indent, statement.indent_alt
        if waiting is not None:
            if width > levels[-1][0]:
                levels.append((width, alt))
                owners.append(waiting.keyword)
            elif waiting.has_colon:
                report(statement, "E702", INDENT,
                       f"Expected an indented block after the '{waiting.keyword}' statement "
                       f"on line {waiting.first_line}.",
                       "Indent the lines that belong to the block (for example by 4 spaces).")
            waiting = None
        elif width > levels[-1][0]:
            report(statement, "E701", INDENT, "Unexpected indent.",
                   "Remove the extra indentation, or end the line above with ':' "
                   "if it should start a block.")
            levels.append((width, alt))
            owners.append(owners[-1])
        else:
            while width < levels[-1][0]:
                levels.pop()
                owners.pop()
            if width != levels[-1][0]:
                report(statement, "E703", INDENT,
                       "Unindent does not match any outer indentation level.",
                       "Line this statement up exactly with the block it belongs to.")
                levels.append((width, alt))
                owners.append(owners[-1])
            elif alt != levels[-1][1]:
                report(statement, "E704", INDENT,
                       "Inconsistent use of tabs and spaces in indentation.",
                       "Indent with spaces only (4 per level is the Python convention).")
        depth = len(levels) - 1
        for deeper in [level for level in last_at if level > depth]:
            del last_at[deeper]

        keyword = statement.keyword if statement.header else None
        if keyword in _PY_FOLLOWS:
            allowed, message = _PY_FOLLOWS[keyword]
            if last_at.get(depth) not in allowed:
                report(statement, "E705", BLOCK, message,
                       f"Put '{keyword}' at the same indentation as its matching statement.")
        if keyword == "case" and owners[-1] != "match":
            report(statement, "E708", BLOCK, "'case' outside a 'match' statement.",
                   "Put 'case' lines inside a 'match value:' block.")
        _python_pairing(statement, owners, report)
        last_at[depth] = keyword or "statement"
        if statement.header:
            if statement.inline_body:
                inline_owner = keyword
            else:
                waiting = statement
    if waiting is not None and waiting.has_colon:
        problems.append(at(waiting.last, Check.BLOCKS, "E702", INDENT,
                           f"Expected an indented block after the '{waiting.keyword}' statement "
                           f"on line {waiting.first_line}, but the input ended.",
                           hint="Add the indented body of the block.",
                           statement=waiting.index))
    return problems


def _python_pairing(statement: Statement, owners: list, report) -> None:
    """break / continue need a loop around them; return needs a function."""
    keyword = statement.keyword
    if keyword in ("break", "continue"):
        for owner in reversed(owners):
            if owner in _LOOPS:
                return
            if owner in ("def", "class"):
                break
        report(statement, "E706", BLOCK, f"'{keyword}' outside a loop.",
               f"'{keyword}' can only be used inside a 'for' or 'while' loop.")
    elif keyword == "return" and "def" not in owners:
        report(statement, "E707", BLOCK, "'return' outside a function.",
               "'return' can only be used inside a function defined with 'def'.")


# --------------------------------------------------------------- C family

def _c_family(statements: list[Statement]) -> list[Diagnostic]:
    problems: list[Diagnostic] = []
    open_blocks: list[Statement] = []

    def report(statement: Statement, code: str, message: str, hint: str):
        problems.append(at(statement.first, Check.BLOCKS, code, BLOCK, message,
                           hint=hint, statement=statement.index))

    for index, statement in enumerate(statements):
        if statement.kind == "block_end":
            if open_blocks:
                open_blocks.pop()
            continue
        # Headers without braces ("if (x)" on its own) govern the next statement.
        braceless = []
        position = index - 1
        while position >= 0 and statements[position].ended_by == "header":
            braceless.append(statements[position])
            position -= 1
        enclosing = open_blocks + braceless[::-1]

        if statement.first.text == "else" and not _follows_if(statements, index):
            report(statement, "E705", "'else' without a matching 'if'.",
                   "An 'else' must come right after the block or statement of an 'if'.")
        if statement.kind == "case" and not any(block.keyword == "switch" for block in enclosing):
            report(statement, "E708", f"'{statement.first.text}' label outside a 'switch' block.",
                   "Put case labels inside switch (value) { ... }.")
        if statement.keyword in ("break", "continue"):
            targets = _LOOPS | ({"switch"} if statement.keyword == "break" else set())
            if not any(block.keyword in targets for block in enclosing):
                report(statement, "E706", f"'{statement.keyword}' outside a loop.",
                       f"'{statement.keyword}' can only be used inside a loop"
                       + (" or a switch." if statement.keyword == "break" else "."))
        if statement.ended_by == "{":
            open_blocks.append(statement)
    return problems


def _follows_if(statements: list[Statement], index: int) -> bool:
    """Does the statement before ``index`` end an 'if' (or 'else if') branch?

    Braced:      if (x) { ... } else ...      the '}' closes an 'if' block
    Not braced:  if (x) y = 1; else ...       the statement two back is an 'if' header
    A plain 'else' branch can never be followed by another 'else'.
    """
    if index == 0:
        return False
    previous = statements[index - 1]
    if previous.kind == "block_end":
        if previous.opener is None:
            return False
        return _is_if_header(statements[previous.opener])
    return index >= 2 and statements[index - 2].ended_by == "header" and \
        _is_if_header(statements[index - 2])


def _is_if_header(statement: Statement) -> bool:
    plain_else = statement.first.text == "else" and (
        len(statement.code) == 1 or statement.code[1].text != "if"
    )
    return statement.kind == "if" and not plain_else
