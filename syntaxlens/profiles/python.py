"""Lexical rules for Python 3.

The keyword list matches Python's own ``keyword.kwlist``, and the number
grammar is taken from CPython's ``Lib/tokenize.py``, so both accept exactly
what Python accepts (the test suite checks this against the real modules).
"""

from .base import LanguageProfile

KEYWORDS = frozenset(
    """
    False None True and as assert async await break class continue def del elif else
    except finally for from global if import in is lambda nonlocal not or pass raise
    return try while with yield
    """.split()
)

# "=" and the augmented assignments are listed as operators: the operator check
# treats assignment like any other operator (x = 5 + * 2 is an operator error).
OPERATORS = frozenset(
    """
    + - * ** / // % @ << >> & | ^ ~ < > <= >= == != :=
    = += -= *= /= //= %= @= &= |= ^= >>= <<= **=
    """.split()
)

DELIMITERS = frozenset("( ) [ ] { } , : . ; -> ...".split())

# Numbers, following CPython's tokenize module.  Underscores may separate digits.
_DIGITS = r"[0-9](?:_?[0-9])*"
_EXPONENT = rf"[eE][-+]?{_DIGITS}"
_POINT_FLOAT = rf"(?:{_DIGITS}\.(?:{_DIGITS})?|\.{_DIGITS})(?:{_EXPONENT})?"  # 3.14  .5  5.  1.5e3
_FLOAT = rf"(?:{_POINT_FLOAT}|{_DIGITS}{_EXPONENT})"                           # ... or 1e10
_IMAGINARY = rf"(?:{_FLOAT}|{_DIGITS})[jJ]"                                    # 3j  1.5j
_INTEGER = (
    r"(?:0[xX](?:_?[0-9a-fA-F])+"   # hexadecimal  0x1F
    r"|0[bB](?:_?[01])+"            # binary       0b1010
    r"|0[oO](?:_?[0-7])+"           # octal        0o17
    r"|0(?:_?0)*"                   # zero         0, 00
    r"|[1-9](?:_?[0-9])*)"          # decimal      42, 1_000
)
NUMBER = rf"(?:{_IMAGINARY}|{_FLOAT}|{_INTEGER})"

PYTHON = LanguageProfile(
    key="python",
    name="Python",
    family="python",
    extensions=(".py", ".pyw"),
    keywords=KEYWORDS,
    operators=OPERATORS,
    delimiters=DELIMITERS,
    line_comment="#",
    block_comment=None,
    string_quotes="\"'",
    char_quote=None,
    triple_quotes="\"'",
    # r"raw", b"bytes", f"format", t"template" and their combinations (rb, fr, ...).
    string_prefix=r"[rR][bBfFtT]?|[bBfFtT][rR]?|[uU]",
    escapes_span_lines=True,
    line_continuation=True,
    name_pattern=r"[^\W\d]\w*",  # a letter or "_", then letters, digits or "_"
    number_pattern=NUMBER,
)
