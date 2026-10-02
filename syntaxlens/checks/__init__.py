"""The eight syntax checks.

Each check is a separate module with one function, ``check(context)``, that
returns the problems it finds.  Every kind of error belongs to exactly one
check, so the same mistake is never reported twice.

    1 delimiters   brackets ( ) [ ] { } are opened and closed in the right order
    2 literals     strings and character literals are closed and well formed
    3 terminators  ';' ends C-family statements, ':' ends Python headers
    4 operators    operators have values on both sides (uses expressions.py)
    5 control      if / for / while / switch / def / class headers are well formed
    6 identifiers  names follow the naming rules and are not reserved words
    7 blocks       indentation (Python) and block pairing (else needs an if, ...)
    8 lexical      illegal characters, malformed numbers, unclosed comments
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..diagnostics import Diagnostic
from ..lexer import LexResult
from ..profiles.base import LanguageProfile
from ..source import Source
from ..structure import Statement
from ..tokens import Token


@dataclass
class Context:
    """Everything a check may look at."""

    source: Source
    lex: LexResult
    statements: list[Statement]
    statement_of: dict[tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for statement in self.statements:
            for token in statement.tokens:
                self.statement_of[(token.line, token.col)] = statement.index

    @property
    def profile(self) -> LanguageProfile:
        return self.lex.profile

    @property
    def python(self) -> bool:
        return self.lex.profile.family == "python"

    def statement_index(self, token: Token) -> int | None:
        """Index of the statement containing ``token`` (None for comments)."""
        return self.statement_of.get((token.line, token.col))


def run_all(context: Context) -> list[Diagnostic]:
    """Run the eight checks and collect everything they report."""
    from . import (
        blocks,
        control,
        delimiters,
        identifiers,
        lexical,
        literals,
        operators,
        terminators,
    )

    diagnostics: list[Diagnostic] = []
    for module in (delimiters, literals, terminators, operators,
                   control, identifiers, blocks, lexical):
        diagnostics.extend(module.check(context))
    return diagnostics
