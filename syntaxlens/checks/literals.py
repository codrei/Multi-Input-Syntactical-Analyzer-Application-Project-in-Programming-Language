"""Check 2: string and character literals.

The lexer already marks every literal whose closing quote is missing (an
unclosed string stops at the end of its line).  This check turns those marks
into errors that name the missing quote.  It also checks character literals
(Java, C): 'a' must contain exactly one character or one escape such as '\\n'.
"""

from __future__ import annotations

import re

from ..diagnostics import Check, Diagnostic, at
from ..lexer import CURLY_DOUBLE, CURLY_SINGLE
from ..tokens import Issue, Token, TokenKind
from . import Context

#: A single character, or one escape sequence: \n, \', \\, A, \101 ...
_ONE_CHAR = re.compile(r"[^\\]|\\(?:u+[0-9a-fA-F]{4}|[0-7]{1,3}|.)", re.DOTALL)

_QUOTE_NAMES = {'"': "double quote", "'": "single quote", "`": "backtick"}


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for token in context.lex.tokens:
        statement = context.statement_index(token)
        if token.issue is Issue.UNTERMINATED_STRING:
            diagnostics.append(_unclosed(token, statement))
        elif token.kind is TokenKind.CHAR:
            problem = _bad_char_literal(token, statement)
            if problem:
                diagnostics.append(problem)
    return diagnostics


def _unclosed(token: Token, statement: int | None) -> Diagnostic:
    body = token.text.lstrip("rRbBuUfFtTL@$")
    quote = body[:1]
    if body.startswith(quote * 3):
        return at(token, Check.LITERALS, "E201", "String Literal Error",
                  f"Unclosed triple-quoted string. Missing the closing {quote * 3} quotes.",
                  hint="The string runs to the end of the input; add the closing quotes.",
                  statement=statement)
    hint = f"Add the closing {_QUOTE_NAMES.get(quote, 'quote')} {quote} at the end of the text."
    if any(char in token.text for char in CURLY_DOUBLE + CURLY_SINGLE):
        hint = "The text contains a curly quote; replace it with a straight quote."
    if token.kind is TokenKind.CHAR:
        return at(token, Check.LITERALS, "E202", "Character Literal Error",
                  "Unclosed character literal. Missing matching single quote \"'\".",
                  hint=hint, statement=statement)
    quote_text = "'\"'" if quote == '"' else f"\"{quote}\""
    return at(token, Check.LITERALS, "E201", "String Literal Error",
              f"Unclosed string literal. Missing matching {_QUOTE_NAMES.get(quote, 'quote')} "
              f"{quote_text}.",
              hint=hint, statement=statement)


def _bad_char_literal(token: Token, statement: int | None) -> Diagnostic | None:
    if token.issue is not None:
        return None
    inner = token.text[1:-1]
    if inner == "":
        return at(token, Check.LITERALS, "E203", "Character Literal Error",
                  "Empty character literal ''. A char must hold exactly one character.",
                  hint="Use ' ' for a space, or a String \"\" for empty text.",
                  statement=statement)
    if _ONE_CHAR.fullmatch(inner):
        return None
    return at(token, Check.LITERALS, "E204", "Character Literal Error",
              f"Character literal {token.text} holds more than one character.",
              hint=f"A char holds one character; use double quotes for text: \"{inner}\".",
              statement=statement)
