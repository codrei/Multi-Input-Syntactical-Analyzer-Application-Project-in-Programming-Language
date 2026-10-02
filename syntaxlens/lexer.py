r"""The lexer (tokenizer): turns source text into a list of tokens.

How it works
------------
Every token pattern of a language is joined into ONE regular expression, the
*master pattern*.  Each alternative is a named group, for example::

    (?P<LINE_COMMENT>#[^\n]*) | (?P<STRING>"[^"\n]*") | (?P<NAME>[A-Za-z_]\w*) | ...

Starting at offset 0, we ask the master pattern to match at the current
offset.  The name of the alternative that matched (``match.lastgroup``) tells
us what kind of token was found.  We record the token, jump to the end of the
match and repeat until the text is used up: a single left-to-right pass.

Three rules make this reliable:

1. **Order matters.**  Python's ``re`` takes the *first* alternative that
   matches, not the longest.  So comments and strings are tried before
   operators (``//`` starts a comment in Java; it is not two slashes), and
   operators are sorted longest first (``**=`` before ``**`` before ``*``).
2. **Strings and comments are single tokens.**  A literal such as
   ``"if (x > 0)"`` is matched whole, so the code-like text inside it is never
   seen by the syntax checks.
3. **The lexer never stops.**  The last alternative matches any single
   character, so a character the language does not allow (``$`` in Python,
   curly quotes pasted from Word) becomes an INVALID token and lexing goes on.
   An unclosed string ends at the end of its line, so the next line is read
   normally.  Problems are only *marked* on tokens (see ``tokens.Issue``); the
   syntax checks decide how to report them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache

from .profiles.base import LanguageProfile
from .source import Source
from .tokens import Issue, Token, TokenKind

#: Characters that look like spaces but are rejected by compilers.  They usually
#: arrive when code is copied out of a PDF, a Word document or a web page.
ODD_SPACES = "\u00a0\u1680\u2000-\u200b\u202f\u205f\u2060\u3000\ufeff"

#: Curly ("smart") quotes produced by word processors, and look-alike primes.
CURLY_DOUBLE = "\u201c\u201d\u201e\u201f\u2033"
CURLY_SINGLE = "\u2018\u2019\u201a\u201b\u2032"

#: Letters, digits, "_" or ".digit" glued to the end of a number, as in "2abc",
#: "0b102" or "3.14.15".  Their presence makes the whole run one bad token.
_NUMBER_TAIL = re.compile(r"(?:\w|\.(?=\d))+")

#: Master-pattern groups that turn directly into tokens: group -> (kind, issue).
_DIRECT_GROUPS = {
    "LINE_COMMENT": (TokenKind.COMMENT, None),
    "BLOCK_COMMENT": (TokenKind.COMMENT, None),
    "BLOCK_COMMENT_OPEN": (TokenKind.COMMENT, Issue.UNTERMINATED_COMMENT),
    "TRIPLE_STRING": (TokenKind.STRING, None),
    "TRIPLE_STRING_OPEN": (TokenKind.STRING, Issue.UNTERMINATED_STRING),
    "STRING": (TokenKind.STRING, None),
    "STRING_OPEN": (TokenKind.STRING, Issue.UNTERMINATED_STRING),
    "CHAR": (TokenKind.CHAR, None),
    "CHAR_OPEN": (TokenKind.CHAR, Issue.UNTERMINATED_STRING),
    "CURLY_QUOTED": (TokenKind.INVALID, Issue.CURLY_QUOTES),
    "ILLEGAL": (TokenKind.INVALID, Issue.ILLEGAL_CHARACTER),
}


@dataclass
class LexResult:
    """Everything the lexer produced for one input."""

    tokens: list[Token]
    profile: LanguageProfile
    #: Lines ending in a backslash that joins them to the next line (Python, C).
    continued_lines: set[int] = field(default_factory=set)
    #: Look-alike spaces found between tokens, as (line, column, character).
    odd_spaces: list[tuple[int, int, str]] = field(default_factory=list)


def tokenize(source: Source, profile: LanguageProfile) -> LexResult:
    """Split ``source`` into tokens using the rules in ``profile``."""
    master = _master_pattern(profile)
    text = source.text
    result = LexResult(tokens=[], profile=profile)
    offset = 0
    # Every position matches some alternative: NEWLINE matches "\n" and ILLEGAL
    # matches any other character, so the loop always moves forward.
    while offset < len(text):
        match = master.match(text, offset)
        group, end, lexeme = match.lastgroup, match.end(), match.group()

        if group in ("NEWLINE", "SPACE"):
            pass  # layout between tokens; indentation is measured later, from the lines
        elif group == "CONTINUATION":
            result.continued_lines.add(source.position(offset)[0])
        elif group == "ODD_SPACE":
            result.odd_spaces.append((*source.position(offset), lexeme))
        else:
            issue = None
            if group == "NUMBER":
                end, kind, issue = _check_number_end(text, offset, end)
            elif group == "NAME":
                kind = TokenKind.KEYWORD if lexeme in profile.keywords else TokenKind.IDENTIFIER
            elif group == "PUNCT":
                kind = TokenKind.OPERATOR if lexeme in profile.operators else TokenKind.DELIMITER
            else:
                kind, issue = _DIRECT_GROUPS[group]
            result.tokens.append(_make_token(source, kind, offset, end, issue))
        offset = end
    return result


def _check_number_end(text: str, start: int, end: int) -> tuple[int, TokenKind, Issue | None]:
    """Look at what follows a number.

    "12" followed by a space or an operator is a fine number.  But in "2abc",
    "0b102" or "3.14.15" the number runs straight into letters, digits or
    another ".digits", so the whole run becomes one bad token.  A plain integer
    followed by letters ("2abc", "1st") is most likely a name that starts with
    a digit; anything else is a malformed number.
    """
    tail = _NUMBER_TAIL.match(text, end)
    if tail is None:
        return end, TokenKind.NUMBER, None
    if text[start:end].isdigit() and text[end].isalpha():
        return tail.end(), TokenKind.INVALID, Issue.NAME_STARTS_WITH_DIGIT
    return tail.end(), TokenKind.INVALID, Issue.MALFORMED_NUMBER


def _make_token(
    source: Source, kind: TokenKind, start: int, end: int, issue: Issue | None
) -> Token:
    line, col = source.position(start)
    end_line, last_col = source.position(end - 1)
    return Token(kind, source.text[start:end], line, col, end_line, last_col + 1, issue)


@cache
def _master_pattern(profile: LanguageProfile) -> re.Pattern[str]:
    """Build the combined pattern described at the top of this module.

    It is built once per language and then cached.
    """
    alternatives: list[tuple[str, str]] = [
        ("NEWLINE", r"\n"),
        ("SPACE", r"[ \t\f]+"),
        ("ODD_SPACE", f"[{ODD_SPACES}]"),
    ]
    if profile.line_continuation:
        alternatives.append(("CONTINUATION", r"\\\n"))
    if profile.block_comment:
        opener, closer = (re.escape(marker) for marker in profile.block_comment)
        alternatives.append(("BLOCK_COMMENT", rf"{opener}[\s\S]*?{closer}"))
        alternatives.append(("BLOCK_COMMENT_OPEN", rf"{opener}[\s\S]*"))  # never closed
    if profile.line_comment:
        alternatives.append(("LINE_COMMENT", rf"{re.escape(profile.line_comment)}[^\n]*"))
    alternatives += _literal_patterns(profile)
    symbols = sorted(profile.operators | profile.delimiters, key=len, reverse=True)
    alternatives += [
        ("NUMBER", profile.number_pattern),
        ("NAME", profile.name_pattern),
        ("PUNCT", "|".join(re.escape(symbol) for symbol in symbols)),
        ("ILLEGAL", r"."),
    ]
    return re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in alternatives))


def _literal_patterns(profile: LanguageProfile) -> list[tuple[str, str]]:
    """Patterns for string, character and curly-quoted literals.

    Each literal kind comes as a pair: the complete literal first, then an
    "_OPEN" version that only matches when no closing quote exists.  Triple
    quotes are tried before single ones; otherwise the empty string ""
    would steal the start of a triple-quoted string.
    """
    prefix = f"(?:{profile.string_prefix})?" if profile.string_prefix else ""
    # Inside a literal a backslash escapes the next character.  In Python it may
    # even escape a line break, continuing the string on the next line.
    escape = r"\\[\s\S]" if profile.escapes_span_lines else r"\\."
    patterns: list[tuple[str, str]] = []

    if profile.triple_quotes:
        complete = "|".join(
            rf"{q * 3}(?:[^{q}\\]|\\[\s\S]|{q}(?!{q}{q}))*{q * 3}" for q in profile.triple_quotes
        )
        opened = "|".join(q * 3 for q in profile.triple_quotes)
        patterns.append(("TRIPLE_STRING", f"{prefix}(?:{complete})"))
        patterns.append(("TRIPLE_STRING_OPEN", rf"{prefix}(?:{opened})[\s\S]*"))  # runs to the end

    for group, quotes, allowed_prefix in (
        ("STRING", profile.string_quotes, prefix),
        ("CHAR", profile.char_quote or "", ""),
    ):
        if not quotes:
            continue
        bodies = [rf"{q}(?:[^{q}\\\n]|{escape})*" for q in quotes]
        complete = "|".join(body + q for body, q in zip(bodies, quotes, strict=True))
        opened = "|".join(rf"{body}\\?" for body in bodies)  # stops at the end of the line
        patterns.append((group, f"{allowed_prefix}(?:{complete})"))
        patterns.append((f"{group}_OPEN", f"{allowed_prefix}(?:{opened})"))

    # Text opened with a curly quote ends at the next quote of the same style
    # (curly or straight) or at the end of the line, so one bad quote does not
    # swallow the rest of the line.
    d, s = CURLY_DOUBLE, CURLY_SINGLE
    patterns.append(("CURLY_QUOTED", rf"""[{d}][^\n{d}"]*[{d}"]?|[{s}][^\n{s}']*[{s}']?"""))
    return patterns
