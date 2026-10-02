"""Lexical rules for C-family languages.

Phase 1 defines Java.  C, C++, C# and JavaScript share most of these rules
and are added in Phase 3.
"""

from .base import LanguageProfile

# Reserved words from the Java Language Specification (JLS 17, section 3.9),
# plus the literals true, false and null, which are also reserved.
JAVA_KEYWORDS = frozenset(
    """
    abstract assert boolean break byte case catch char class const continue default do
    double else enum extends final finally float for goto if implements import
    instanceof int interface long native new package private protected public return
    short static strictfp super switch synchronized this throw throws transient try void
    volatile while true false null
    """.split()
)

# JLS 3.12.  ":" is classed as a delimiter (it also ends case labels), as in Python.
JAVA_OPERATORS = frozenset(
    """
    = > < ! ~ ? -> == >= <= != && || ++ -- + - * / & | ^ % << >> >>>
    += -= *= /= &= |= ^= %= <<= >>= >>>=
    """.split()
)

# JLS 3.11 separators, plus ":".
JAVA_DELIMITERS = frozenset("( ) { } [ ] ; , . ... @ :: :".split())

# Java numbers.  Underscores may appear between digits: 1_000_000.
_DIGITS = r"[0-9](?:[0-9_]*[0-9])?"
_EXPONENT = rf"[eE][-+]?{_DIGITS}"
_FLOAT = (
    rf"(?:(?:{_DIGITS}\.(?:{_DIGITS})?|\.{_DIGITS})(?:{_EXPONENT})?[fFdD]?"  # 3.14  .5  2.5e-3f
    rf"|{_DIGITS}{_EXPONENT}[fFdD]?"                                         # 1e10
    rf"|{_DIGITS}[fFdD])"                                                    # 5f  2d
)
_INTEGER = (
    r"(?:0[xX][0-9a-fA-F](?:[0-9a-fA-F_]*[0-9a-fA-F])?"  # hexadecimal  0x1F
    r"|0[bB][01](?:[01_]*[01])?"                         # binary       0b1010
    r"|0(?:[0-7_]*[0-7])?"                               # octal 017, and plain 0
    r"|[1-9](?:[0-9_]*[0-9])?)[lL]?"                     # decimal; L marks a long
)
JAVA_NUMBER = rf"(?:{_FLOAT}|{_INTEGER})"

JAVA = LanguageProfile(
    key="java",
    name="Java",
    family="c",
    extensions=(".java",),
    keywords=JAVA_KEYWORDS,
    operators=JAVA_OPERATORS,
    delimiters=JAVA_DELIMITERS,
    line_comment="//",
    block_comment=("/*", "*/"),
    string_quotes='"',
    char_quote="'",
    triple_quotes='"',  # text blocks: """ ... """ (Java 15+)
    string_prefix="",
    escapes_span_lines=False,
    line_continuation=False,
    name_pattern=r"(?:[^\W\d]|\$)(?:\w|\$)*",  # Java also allows "$" in names
    number_pattern=JAVA_NUMBER,
)
