"""The data that describes one programming language to the lexer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageProfile:
    """The lexical rules of one language, stored as plain data.

    The lexer contains no language-specific code.  Everything that differs
    between languages (keywords, operators, comment markers, how strings and
    numbers are written) lives in a profile.  Supporting another language
    mostly means writing another profile.
    """

    key: str                               # id used by the CLI and web app, e.g. "java"
    name: str                              # display name, e.g. "Java"
    family: str                            # "python" or "c": selects the statement rules later
    extensions: tuple[str, ...]            # file extensions that select this language
    keywords: frozenset[str]               # reserved words
    operators: frozenset[str]              # symbols that compute, compare or assign: + == += &&
    delimiters: frozenset[str]             # punctuation that structures code: ( ) { } , ; : .
    line_comment: str | None               # "#" or "//"
    block_comment: tuple[str, str] | None  # ("/*", "*/"), or None when the language has none
    string_quotes: str                     # quote characters that start a string literal
    char_quote: str | None                 # "'" when 'x' is a character literal (Java, C)
    triple_quotes: str                     # quote characters that may be tripled: """text"""
    string_prefix: str                     # regex for letters allowed before a quote: r"..."
    escapes_span_lines: bool               # may a backslash inside a string escape a line break?
    line_continuation: bool                # may a backslash at a line's end join two lines?
    name_pattern: str                      # regex for identifiers
    number_pattern: str                    # regex for valid numeric literals
