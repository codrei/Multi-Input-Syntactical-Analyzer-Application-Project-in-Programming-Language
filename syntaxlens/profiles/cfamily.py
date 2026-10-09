"""Lexical rules for C-family languages.

Phase 1 defines Java.  C, C++, C# and JavaScript share most of these rules
and are added in Phase 3.
"""

from .base import LanguageProfile
from .rules import DISCARDED_VALUE_WARNING, LanguageRules

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
    rules=LanguageRules(
        # 'x + 1;' is "not a statement"; calls, ++/--, 'new', this.f() and lambdas are fine.
        self_reference_statements=True,
        arrow_statements="->",
        call_operators=frozenset({"->"}),
        parameter_modifiers=frozenset({"final"}),
    ),
)

# ---------------------------------------------------------------------------
# Shared helper: numeric literals for C, C++ and C#
# ---------------------------------------------------------------------------

def _number(sep: str, int_suffix: str, float_suffix: str) -> str:
    """Build a number regex.  ``sep`` is the digit separator ("" for none)."""
    digits = rf"[0-9](?:[0-9{sep}]*[0-9])?"
    hex_digits = rf"[0-9a-fA-F](?:[0-9a-fA-F{sep}]*[0-9a-fA-F])?"
    exponent = rf"[eE][-+]?{digits}"
    floating = (
        rf"(?:(?:{digits}\.(?:{digits})?|\.{digits})(?:{exponent})?{float_suffix}"
        rf"|{digits}{exponent}{float_suffix})"
    )
    integer = (
        rf"(?:0[xX]{hex_digits}"                  # hexadecimal  0x1F
        rf"|0[bB][01](?:[01{sep}]*[01])?"         # binary       0b1010
        rf"|0(?:[0-7{sep}]*[0-7])?"               # octal 017, and plain 0
        rf"|[1-9](?:[0-9{sep}]*[0-9])?){int_suffix}"  # decimal
    )
    return rf"(?:{floating}|{integer})"


_C_INT_SUFFIX = r"(?:[uU](?:ll|LL|[lL])?|(?:ll|LL|[lL])[uU]?)?"   # u, l, ul, ll, ull
_C_FLOAT_SUFFIX = r"[fFlL]?"

# ---------------------------------------------------------------------------
# C (C17, plus a few C23 words)
# ---------------------------------------------------------------------------

C_KEYWORDS = frozenset(
    """
    alignas alignof auto bool break case char const constexpr continue default
    do double else enum extern false float for goto if inline int long
    nullptr register restrict return short signed sizeof static
    static_assert struct switch thread_local true typedef typeof union
    unsigned void volatile while
    _Alignas _Alignof _Atomic _Bool _Complex _Generic _Imaginary _Noreturn
    _Static_assert _Thread_local
    """.split()
)

C_OPERATORS = frozenset(
    """
    = > < ! ~ ? -> == >= <= != && || ++ -- + - * / & | ^ % << >>
    += -= *= /= &= |= ^= %= <<= >>=
    """.split()
)

# "#" starts preprocessor lines such as #include and #define.
C_DELIMITERS = frozenset("( ) { } [ ] ; , . ... : #".split())

C = LanguageProfile(
    key="c",
    name="C",
    family="c",
    extensions=(".c", ".h"),
    keywords=C_KEYWORDS,
    operators=C_OPERATORS,
    delimiters=C_DELIMITERS,
    line_comment="//",
    block_comment=("/*", "*/"),
    string_quotes='"',
    char_quote="'",
    triple_quotes="",
    string_prefix=r"(?:u8|[uUL])?",
    escapes_span_lines=False,
    line_continuation=True,  # a trailing backslash continues a line (macros)
    name_pattern=r"[^\W\d]\w*",
    number_pattern=_number("", _C_INT_SUFFIX, _C_FLOAT_SUFFIX),
    rules=LanguageRules(
        preprocessor_lines=True,
        discarded_value=DISCARDED_VALUE_WARNING,   # 'x + 1;' is legal C
        call_operators=frozenset({"->"}),
        void_parameter=True,
        variadic_parameter=True,
        parameter_names_optional=True,
    ),
)

# ---------------------------------------------------------------------------
# C++ (ISO C++20)
# ---------------------------------------------------------------------------

CPP_KEYWORDS = frozenset(
    """
    alignas alignof and and_eq asm auto bitand bitor bool break case catch
    char char8_t char16_t char32_t class compl concept const consteval
    constexpr constinit const_cast continue co_await co_return co_yield
    decltype default delete do double dynamic_cast else enum explicit export
    extern false float for friend goto if inline int long mutable namespace
    new noexcept not not_eq nullptr operator or or_eq private protected
    public register reinterpret_cast requires return short signed sizeof
    static static_assert static_cast struct switch template this
    thread_local throw true try typedef typeid typename union unsigned using
    virtual void volatile wchar_t while xor xor_eq
    """.split()
)

CPP_OPERATORS = frozenset(
    """
    = > < ! ~ ? -> == >= <= != && || ++ -- + - * / & | ^ % << >> <=>
    += -= *= /= &= |= ^= %= <<= >>=
    """.split()
)

# "::" is the scope operator (std::cout), classed as a delimiter like Java's "::".
CPP_DELIMITERS = frozenset("( ) { } [ ] ; , . ... :: : #".split())

CPP = LanguageProfile(
    key="cpp",
    name="C++",
    family="c",
    extensions=(".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"),
    keywords=CPP_KEYWORDS,
    operators=CPP_OPERATORS,
    delimiters=CPP_DELIMITERS,
    line_comment="//",
    block_comment=("/*", "*/"),
    string_quotes='"',
    char_quote="'",
    triple_quotes="",
    string_prefix=r"(?:u8|[uUL])?",
    escapes_span_lines=False,
    line_continuation=True,
    name_pattern=r"[^\W\d]\w*",
    number_pattern=_number("'", _C_INT_SUFFIX, _C_FLOAT_SUFFIX),  # 1'000'000 (C++14)
    rules=LanguageRules(
        preprocessor_lines=True,
        access_labels=True,
        stream_chains=True,
        discarded_value=DISCARDED_VALUE_WARNING,
        generic_arguments=True,
        call_operators=frozenset({"->"}),
        void_parameter=True,
        variadic_parameter=True,
        parameter_names_optional=True,
    ),
)

# ---------------------------------------------------------------------------
# C# (reserved keywords only: words like var, async and await are
# "contextual" and stay ordinary identifiers)
# ---------------------------------------------------------------------------

CSHARP_KEYWORDS = frozenset(
    """
    abstract as base bool break byte case catch char checked class const
    continue decimal default delegate do double else enum event explicit
    extern false finally fixed float for foreach goto if implicit in int
    interface internal is lock long namespace new null object operator out
    override params private protected public readonly ref return sbyte sealed
    short sizeof stackalloc static string struct switch this throw true try
    typeof uint ulong unchecked unsafe ushort using virtual void volatile while
    """.split()
)

CSHARP_OPERATORS = frozenset(
    """
    = > < ! ~ ? ?? ??= ?. -> => == >= <= != && || ++ -- + - * / & | ^ % << >> >>>
    += -= *= /= &= |= ^= %= <<= >>= >>>= ..
    """.split()
)

CSHARP_DELIMITERS = frozenset("( ) { } [ ] ; , . :: : #".split())

CSHARP = LanguageProfile(
    key="csharp",
    name="C#",
    family="c",
    extensions=(".cs",),
    keywords=CSHARP_KEYWORDS,
    operators=CSHARP_OPERATORS,
    delimiters=CSHARP_DELIMITERS,
    line_comment="//",
    block_comment=("/*", "*/"),
    string_quotes='"',
    char_quote="'",
    triple_quotes='"',  # raw string literals: """ ... """ (C# 11)
    string_prefix=r"[$@]{0,2}",  # $"interpolated", @"verbatim"
    escapes_span_lines=False,
    line_continuation=False,
    name_pattern=r"@?[^\W\d]\w*",  # @class lets a keyword be used as a name
    number_pattern=_number("_", r"(?:[uU][lL]?|[lL][uU]?|[fFdDmM])?", r"[fFdDmM]?"),
    rules=LanguageRules(
        preprocessor_lines=True,                   # #region, #if, #nullable
        contextual_modifiers=frozenset({"async", "partial", "required", "global"}),
        await_prefix=True,
        # 'x + 1;' is "not a statement"; calls, ++/--, 'new', 'await' and accessors are fine.
        generic_arguments=True,
        call_operators=frozenset({"->", "?.", "!"}),
        accessor_names=frozenset({"get", "set", "init", "add", "remove"}),
        parameter_modifiers=frozenset({"ref", "out", "in", "params", "this"}),
    ),
)
