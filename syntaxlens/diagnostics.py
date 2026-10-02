"""Diagnostics: the errors and warnings that the syntax checks report.

Every problem found is one :class:`Diagnostic`.  It records which of the
eight checks found it, a stable code (``E401``), a short category label for
the report, a one-sentence explanation, where it is, and optionally a hint
on how to fix it.

Error code ranges follow the check numbers: E1xx delimiters, E2xx literals,
E3xx terminators, E4xx operators, E5xx headers, E6xx identifiers, E7xx
indentation and blocks, E8xx illegal characters.  Warnings use W instead of E.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .tokens import Token


class Check(Enum):
    """The eight syntax checks, as (number, title)."""

    DELIMITERS = (1, "Delimiter & Bracket Matching")
    LITERALS = (2, "String & Character Literals")
    TERMINATORS = (3, "Statement Terminators")
    OPERATORS = (4, "Operator Syntax")
    CONTROL = (5, "Control Structure Headers")
    IDENTIFIERS = (6, "Identifier Naming")
    BLOCKS = (7, "Indentation & Block Structure")
    LEXICAL = (8, "Illegal Characters & Malformed Literals")

    @property
    def number(self) -> int:
        return self.value[0]

    @property
    def title(self) -> str:
        return self.value[1]


class Severity(Enum):
    ERROR = "error"      # the code cannot compile or run
    WARNING = "warning"  # valid code that is very likely a mistake


@dataclass(frozen=True)
class Diagnostic:
    """One problem found in the code (lines and columns count from 1)."""

    check: Check
    code: str                     # stable identifier, e.g. "E401"
    category: str                 # label shown in the report, e.g. "Invalid Operator Sequence"
    message: str                  # the explanation ("Details:" in the report)
    line: int
    col: int
    severity: Severity = Severity.ERROR
    hint: str | None = None       # how to fix it
    statement: int | None = None  # index of the statement it belongs to (for filtering)

    @property
    def is_error(self) -> bool:
        return self.severity is Severity.ERROR


def at(token: Token, check: Check, code: str, category: str, message: str, **extra) -> Diagnostic:
    """Shortcut: a diagnostic located at ``token``."""
    severity = Severity.WARNING if code.startswith("W") else Severity.ERROR
    return Diagnostic(check, code, category, message, token.line, token.col, severity, **extra)
