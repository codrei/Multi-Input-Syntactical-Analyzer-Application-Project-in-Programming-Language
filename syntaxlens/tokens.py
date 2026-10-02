"""Token types: the vocabulary shared by the lexer and every later stage.

A token is the smallest meaningful unit of code: a keyword (``if``), a name
(``total``), an operator (``+=``), a literal (``"hi"``, ``3.14``), a piece of
punctuation (``(``, ``;``) or a comment.  The lexer (lexer.py) produces a list
of tokens, and the syntax checks work on those tokens, never on raw characters.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class TokenCategory(Enum):
    """The eight categories shown in reports, as (plural label, singular label)."""

    KEYWORD = ("Keywords", "Keyword")
    IDENTIFIER = ("Identifiers", "Identifier")
    OPERATOR = ("Operators", "Operator")
    NUMBER = ("Numeric Literals", "Numeric Literal")
    STRING = ("String & Char Literals", "String/Char Literal")
    DELIMITER = ("Delimiters", "Delimiter")
    COMMENT = ("Comments", "Comment")
    INVALID = ("Invalid Tokens", "Invalid Token")

    @property
    def plural(self) -> str:
        return self.value[0]

    @property
    def singular(self) -> str:
        return self.value[1]


class TokenKind(Enum):
    """What a token is.  Slightly finer than a category: strings and chars differ."""

    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    OPERATOR = "operator"
    NUMBER = "number"
    STRING = "string"
    CHAR = "char"
    DELIMITER = "delimiter"
    COMMENT = "comment"
    INVALID = "invalid"

    @property
    def category(self) -> TokenCategory:
        return _CATEGORY_OF_KIND[self]


_CATEGORY_OF_KIND = {
    TokenKind.KEYWORD: TokenCategory.KEYWORD,
    TokenKind.IDENTIFIER: TokenCategory.IDENTIFIER,
    TokenKind.OPERATOR: TokenCategory.OPERATOR,
    TokenKind.NUMBER: TokenCategory.NUMBER,
    TokenKind.STRING: TokenCategory.STRING,
    TokenKind.CHAR: TokenCategory.STRING,
    TokenKind.DELIMITER: TokenCategory.DELIMITER,
    TokenKind.COMMENT: TokenCategory.COMMENT,
    TokenKind.INVALID: TokenCategory.INVALID,
}


class Issue(Enum):
    """A problem the lexer noticed while reading a token.

    The lexer only *marks* problems on tokens; the syntax checks decide how to
    report them.  That keeps the lexer small and lets each check own its errors.
    """

    UNTERMINATED_STRING = "literal is never closed"
    UNTERMINATED_COMMENT = "block comment is never closed"
    MALFORMED_NUMBER = "number is not written correctly"
    NAME_STARTS_WITH_DIGIT = "name starts with a digit"
    ILLEGAL_CHARACTER = "character is not allowed here"
    CURLY_QUOTES = "curly quotes cannot delimit strings"


@dataclass(frozen=True, slots=True)
class Token:
    """One token and where it sits in the source (lines and columns count from 1)."""

    kind: TokenKind
    text: str               # the exact characters from the source (the "lexeme")
    line: int               # where the token starts
    col: int
    end_line: int           # where it ends; differs from `line` only for multi-line tokens
    end_col: int            # column just past the last character
    issue: Issue | None = None

    @property
    def category(self) -> TokenCategory:
        return self.kind.category


def group_by_category(tokens: Iterable[Token]) -> dict[TokenCategory, list[Token]]:
    """Sort tokens into the eight categories.  Every category is present, even if empty."""
    groups: dict[TokenCategory, list[Token]] = {category: [] for category in TokenCategory}
    for token in tokens:
        groups[token.category].append(token)
    return groups
