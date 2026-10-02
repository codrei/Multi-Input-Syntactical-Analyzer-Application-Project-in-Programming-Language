"""Check 8: illegal characters and malformed literals.

The lexer marks every character it cannot use (``$`` in Python, ``#`` in
Java, curly quotes from a word processor), every malformed number
(``3.14.15``, ``0b102``) and every block comment that is never closed.  It
also records invisible look-alike spaces.  This check explains each one.
"""

from __future__ import annotations

import unicodedata

from ..diagnostics import Check, Diagnostic, at
from ..tokens import Issue, Token
from . import Context

_PYTHON_HINTS = {
    "$": "Python names cannot contain '$'.",
    "!": "Python writes 'not x' for negation ('!=' is still fine).",
    "?": "Python has no '?:' operator; use 'a if condition else b'.",
    "`": "Use quotes for strings; backticks are not valid in Python.",
}
_C_HINTS = {
    "#": "'#' is not valid here; comments start with //.",
    "\\": "A backslash is only valid inside strings and character literals.",
    "`": "Use double quotes for strings.",
}


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for token in context.lex.tokens:
        statement = context.statement_index(token)
        if token.issue is Issue.ILLEGAL_CHARACTER:
            diagnostics.append(_illegal(token, context, statement))
        elif token.issue is Issue.CURLY_QUOTES:
            diagnostics.append(at(
                token, Check.LEXICAL, "E804", "Illegal Character",
                f"Curly quotes in {token.text} are not valid string quotes.",
                hint="Replace them with straight quotes \" or ' (curly quotes usually come from "
                     "Word, PDFs or chat apps).",
                statement=statement,
            ))
        elif token.issue is Issue.MALFORMED_NUMBER:
            diagnostics.append(at(
                token, Check.LEXICAL, "E802", "Malformed Number",
                f"'{token.text}' is not a valid number. {_number_reason(token.text, context)}",
                hint="Write the number in a valid form, e.g. 3.14, 42 or 0x1F.",
                statement=statement,
            ))
        elif token.issue is Issue.UNTERMINATED_COMMENT:
            opener, closer = context.profile.block_comment or ("/*", "*/")
            diagnostics.append(at(
                token, Check.LEXICAL, "E803", "Unclosed Comment",
                f"Unclosed block comment '{opener}'. Expected '{closer}' before the end of the input.",
                hint=f"Add '{closer}' where the comment should end.",
                statement=statement,
            ))
    for line, col, char in context.lex.odd_spaces:
        name = unicodedata.name(char, "UNKNOWN").lower()
        diagnostics.append(Diagnostic(
            Check.LEXICAL, "E805", "Illegal Character",
            f"Invisible look-alike space U+{ord(char):04X} ({name}).",
            line, col,
            hint="Replace it with a normal space; it usually comes from copying code out of a "
                 "PDF, Word document or web page.",
        ))
    return diagnostics


def _illegal(token: Token, context: Context, statement: int | None) -> Diagnostic:
    char = token.text
    hints = _PYTHON_HINTS if context.python else _C_HINTS
    if char in hints:
        hint = hints[char]
    elif not char.isprintable():
        hint = "This is an invisible control character; delete it."
    else:
        hint = f"Remove '{char}', or put it inside a string."
    return at(token, Check.LEXICAL, "E801", "Illegal Character",
              f"Character '{char}' (U+{ord(char):04X}) is not allowed in "
              f"{context.profile.name} code here.",
              hint=hint, statement=statement)


def _number_reason(text: str, context: Context) -> str:
    lower = text.lower()
    if text.count(".") > 1:
        return "A number can contain only one decimal point."
    if lower.startswith("0b"):
        return "Binary numbers may only use the digits 0 and 1."
    if lower.startswith("0x"):
        return "Hexadecimal numbers may only use 0-9 and A-F."
    if lower.startswith("0o"):
        return "Octal numbers may only use the digits 0-7."
    if "__" in text or text.endswith("_") or "_." in text or "._" in text:
        return "Underscores may only appear between digits."
    if text[0] == "0" and text[1:2].isdigit():
        if context.python:
            return "Python does not allow leading zeros; use 0o for octal numbers."
        return "A number starting with 0 is octal and may only use the digits 0-7."
    return "Unexpected characters follow the number."
