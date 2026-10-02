"""Check 3: statement terminators.

* **C family (Java, ...):** every simple statement must end with ``;``.  The
  statement builder notices when a statement is complete but the next line
  starts a new one without a ``;`` in between (see structure.py).
* **Python:** a compound statement header (``if``, ``for``, ``while``,
  ``def``, ``class``, ...) must end with ``:``.  Python's indentation rules
  are handled by check 7.
"""

from __future__ import annotations

from ..diagnostics import Check, Diagnostic
from ..structure import is_delim
from . import Context


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for statement in context.statements:
        last = statement.tokens[-1]
        if context.python and statement.header and not statement.has_colon:
            if is_delim(last, "{"):
                hint = "Python marks blocks with ':' and indentation, not '{'. Replace '{' with ':'."
            else:
                line = context.source.line_text(last.line).strip()
                hint = f"Add ':' at the end: {line}:"
            diagnostics.append(Diagnostic(
                Check.TERMINATORS, "E302", "Missing Colon",
                f"Missing colon ':' at the end of the '{statement.keyword}' statement header.",
                last.end_line, last.end_col, hint=hint, statement=statement.index,
            ))
        elif not context.python and statement.missing_terminator:
            what = "the do-while condition" if statement.kind == "do_while_end" else "the statement"
            diagnostics.append(Diagnostic(
                Check.TERMINATORS, "E301", "Missing Semicolon",
                f"Missing semicolon ';' at the end of {what}.",
                last.end_line, last.end_col, hint=f"Add ';' after '{last.text}'.",
                statement=statement.index,
            ))
    return diagnostics
