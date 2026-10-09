"""The statement builder: groups the token stream into statements.

The lexer produces one flat list of tokens.  The syntax checks need to know
where each statement starts and ends, and what kind of statement it is
(assignment, ``if`` header, function call, ...).  This module answers both.

Python
    A statement normally ends at the end of its line.  It continues on the
    next line after a backslash, or while a bracket is still open.  A ``;``
    separates two statements on one line, and a compound header such as
    ``if x: y = 1`` is split at its ``:``.

C family (Java, ...)
    A statement ends at ``;``.  A ``{`` ends a header (``if (...) {``,
    ``class A {``) and opens a block; ``}`` closes it.

Recovering from mistakes
    A bracket left open must not swallow the rest of the file, and a missing
    ``;`` must not glue two statements together.  At every line break inside
    an unfinished statement we therefore ask: does this line end with a
    complete value (``5``, ``x``, ``)``) while the next line starts something
    new (``print(``, ``int y``)?  If so, the statement ends here.  The bracket
    or semicolon check then reports the missing character on this line, and
    the next line is analyzed on its own.  This is how the analyzer keeps
    going after an error on line 2 and still checks line 3 correctly.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lexer import LexResult
from .profiles.rules import DEFAULT_RULES, LanguageRules
from .source import Source
from .tokens import Token, TokenKind

OPENERS = {"(": ")", "[": "]", "{": "}"}
CLOSERS = {")": "(", "]": "[", "}": "{"}

#: Keywords that stand for a value, such as True or this.
VALUE_KEYWORDS = frozenset("True False None true false null this super".split())

#: Assignment operators (Python and C family).
ASSIGNMENT_OPS = frozenset(
    "= += -= *= /= //= %= **= @= &= |= ^= <<= >>= >>>=".split()
)

#: Calls that print output, shown as "Function Call / Output Statement".
OUTPUT_CALLS = frozenset(
    """print System.out.println System.out.print System.out.printf System.out.format
    System.err.println System.err.print System.err.printf
    printf puts putchar fputs fprintf std::printf std::puts
    Console.WriteLine Console.Write Console.Error.WriteLine Console.Error.Write""".split()
)

#: The text shown after "Syntax Check:" in the report, for each statement kind.
KIND_LABELS = {
    "assignment": "Variable Assignment",
    "declaration": "Variable Declaration",
    "if": "Conditional Statement Header",
    "loop": "Loop Header",
    "do_while_end": "Do-While Condition",
    "switch": "Switch / Match Header",
    "case": "Case Label",
    "output": "Function Call / Output Statement",
    "call": "Function Call",
    "function": "Function Definition",
    "method": "Method Declaration",
    "class": "Class Declaration",
    "return": "Return Statement",
    "jump": "Jump Statement",
    "import": "Import Statement",
    "package": "Package Declaration",
    "exception": "Exception Handling",
    "context": "Context Manager (with / using)",
    "decorator": "Decorator",
    "annotation": "Annotation",
    "scope": "Scope Declaration",
    "delete": "Delete Statement",
    "assert": "Assertion",
    "block_end": "Block End",
    "enum_constants": "Enum Constants",
    "label": "Label",
    "preprocessor": "Preprocessor Directive",
    "using": "Using Directive / Alias",
    "namespace": "Namespace Declaration",
    "empty": "Empty Statement",
    "expression": "Expression Statement",
}

PY_COMPOUND = frozenset("if elif else while for def class try except finally with async".split())
PY_HEADER_KINDS = {
    "if": "if", "elif": "if", "else": "if", "while": "loop", "for": "loop",
    "def": "function", "class": "class", "try": "exception", "except": "exception",
    "finally": "exception", "with": "context", "match": "switch", "case": "case",
}
PY_SIMPLE_KINDS = {
    "return": "return", "pass": "jump", "break": "jump", "continue": "jump",
    "import": "import", "from": "import", "raise": "exception", "global": "scope",
    "nonlocal": "scope", "del": "delete", "assert": "assert",
}

C_PAREN_HEADERS = frozenset("if while for switch catch synchronized foreach lock using fixed".split())
C_BARE_HEADERS = frozenset("else do try finally".split())
C_MODIFIERS = frozenset(
    "public private protected static final abstract native synchronized transient volatile "
    "strictfp default sealed "
    # C, C++ and C#
    "typedef extern const inline constexpr explicit friend mutable register template "
    "internal override virtual readonly unsafe".split()
)
C_PRIMITIVES = frozenset("int long short byte char float double boolean void".split())
C_TYPE_DECLARATIONS = frozenset("class interface enum record struct union namespace".split())

#: Keywords that name a type on their own in C, C++ and C# (Java has none of these).
TYPE_WORDS = frozenset(
    "bool string object decimal sbyte ushort uint ulong signed unsigned auto "
    "wchar_t char8_t char16_t char32_t _Bool".split()
)
_TYPE_QUALIFIERS = frozenset("const volatile struct union enum typename".split())
_BASE_TYPE_WORDS = C_PRIMITIVES | TYPE_WORDS
C_HEADER_KINDS = {
    "if": "if", "else": "if", "while": "loop", "for": "loop", "do": "loop",
    "switch": "switch", "try": "exception", "catch": "exception", "finally": "exception",
    "synchronized": "exception", "foreach": "loop", "lock": "context", "fixed": "context",
}
C_SIMPLE_KINDS = {
    "return": "return", "break": "jump", "continue": "jump", "throw": "exception",
    "import": "import", "package": "package", "assert": "assert", "yield": "return",
}
#: Keywords that can only start a new statement (used to spot a missing ';').
C_STATEMENT_STARTERS = (
    C_PRIMITIVES | C_MODIFIERS | C_TYPE_DECLARATIONS | C_PAREN_HEADERS | C_BARE_HEADERS
    | frozenset("return break continue throw case new this super assert package import "
                "typedef using namespace".split())
)

#: Names of the standard C++ streams: ``cout << x`` and ``cin >> x`` are call-like statements.
STREAM_OUT = frozenset("cout cerr clog wcout wcerr wclog".split())
STREAM_IN = frozenset("cin wcin".split())
ACCESS_LABELS = frozenset("public private protected".split())


@dataclass
class Statement:
    """One statement: its tokens (comments excluded) and what we know about it."""

    index: int
    tokens: list[Token]
    kind: str = "expression"
    keyword: str | None = None    # the keyword that starts it: "if", "def", "class", ...
    header: bool = False          # starts a compound statement that owns a block
    ended_by: str = "line"        # "line", ";", "{", "}", ":", "header" or "eof"
    missing_terminator: bool = False   # C family: a needed ';' is absent
    has_colon: bool = False       # Python header that ends with ':'
    inline_body: bool = False     # Python header followed by a statement on the same line
    inline: bool = False          # shares its line with an earlier statement
    indent: int = 0               # Python: indentation width (tab = up to the next multiple of 8)
    indent_alt: int = 0           # same with a tab counted as 1 (spots mixed tabs and spaces)
    opener: int | None = None     # C family "}": index of the header statement it closes
    closer_line: int | None = None    # C family header: line of its matching "}"

    @property
    def first(self) -> Token:
        return self.tokens[0]

    @property
    def last(self) -> Token:
        return self.tokens[-1]

    @property
    def first_line(self) -> int:
        return self.tokens[0].line

    @property
    def last_line(self) -> int:
        return self.tokens[-1].end_line

    @property
    def label(self) -> str:
        return KIND_LABELS.get(self.kind, "Statement")

    @property
    def code(self) -> list[Token]:
        """The tokens without the ';', ':' or '{' that ends the statement."""
        if self.ended_by in (";", "{", ":") and self.tokens[-1].text == self.ended_by:
            return self.tokens[:-1]
        return self.tokens


def build_statements(source: Source, lex: LexResult) -> list[Statement]:
    """Group the tokens into statements, using the rules of the language family."""
    if lex.profile.family == "python":
        return _python_statements(source, lex)
    return _c_statements(lex)


# --------------------------------------------------------------------------- helpers

def is_delim(token: Token, *texts: str) -> bool:
    return token.kind is TokenKind.DELIMITER and token.text in texts


def ends_value(token: Token) -> bool:
    """Can ``token`` be the last token of a complete value?  (x, 5, "s", ')' ...)"""
    if token.kind in (TokenKind.IDENTIFIER, TokenKind.NUMBER, TokenKind.STRING,
                      TokenKind.CHAR, TokenKind.INVALID):
        return True
    return token.text in (")", "]", "++", "--") or token.text in VALUE_KEYWORDS


def top_level(tokens: list[Token]):
    """Yield (index, token, depth) where depth counts the brackets open before the token."""
    depth = 0
    for index, token in enumerate(tokens):
        if is_delim(token, ")", "]", "}"):
            depth = max(0, depth - 1)
        yield index, token, depth
        if is_delim(token, "(", "[", "{"):
            depth += 1


def find_top(tokens: list[Token], *texts: str, start: int = 0) -> int | None:
    """Index of the first token outside all brackets whose text is in ``texts``."""
    for index, token, depth in top_level(tokens):
        if index >= start and depth == 0 and token.text in texts and token.kind not in (
            TokenKind.STRING, TokenKind.CHAR, TokenKind.COMMENT
        ):
            return index
    return None


def split_top(tokens: list[Token], separator: str) -> list[list[Token]]:
    """Split ``tokens`` at every top-level ``separator`` (for example ',')."""
    parts: list[list[Token]] = [[]]
    for _, token, depth in top_level(tokens):
        if depth == 0 and token.text == separator and token.kind in (
            TokenKind.DELIMITER, TokenKind.OPERATOR
        ):
            parts.append([])
        else:
            parts[-1].append(token)
    return parts


def call_name(tokens: list[Token]) -> str | None:
    """'System.out.println' for a statement shaped like a call, else None."""
    parts: list[str] = []
    separators: list[str] = []
    index = 0
    while index < len(tokens) and tokens[index].kind is TokenKind.IDENTIFIER:
        parts.append(tokens[index].text)
        index += 1
        if index < len(tokens) and is_delim(tokens[index], ".", "::"):
            separators.append(tokens[index].text)
            index += 1
            continue
        break
    if parts and index < len(tokens) and is_delim(tokens[index], "("):
        closes = _skip_group(tokens, index)
        # print(...) is a call; so is print("hi) whose ')' was swallowed by an open string.
        if (tokens[-1].text == ")" or closes >= len(tokens) and not is_delim(tokens[-1], ")")) \
                and find_top(tokens, *ASSIGNMENT_OPS) is None:
            name = parts[0]
            for separator, part in zip(separators, parts[1:], strict=False):
                name += separator + part
            return name
    return None


def _call_kind(tokens: list[Token]) -> str | None:
    name = call_name(tokens)
    if name is None:
        return None
    return "output" if name in OUTPUT_CALLS else "call"


def _code_tokens(lex: LexResult) -> list[Token]:
    return [token for token in lex.tokens if token.kind is not TokenKind.COMMENT]


# --------------------------------------------------------------------------- Python

def _python_statements(source: Source, lex: LexResult) -> list[Statement]:
    statements: list[Statement] = []
    for line_tokens in _python_logical_lines(lex):
        indent_text = _leading_whitespace(source.line_text(line_tokens[0].line))
        for position, (tokens, header, has_colon, inline_body) in enumerate(
            _split_python_line(line_tokens)
        ):
            statement = Statement(
                index=len(statements),
                tokens=tokens,
                header=header,
                has_colon=has_colon,
                inline_body=inline_body,
                inline=position > 0,
                indent=_width(indent_text, tab=8),
                indent_alt=_width(indent_text, tab=1),
                ended_by=":" if has_colon else (";" if tokens[-1].text == ";" else "line"),
            )
            _classify_python(statement)
            statements.append(statement)
    return statements


def _python_logical_lines(lex: LexResult) -> list[list[Token]]:
    """Group tokens into logical lines (one or more physical lines)."""
    code = _code_tokens(lex)
    lines: list[list[Token]] = []
    current: list[Token] = []
    depth = 0
    for index, token in enumerate(code):
        current.append(token)
        if is_delim(token, "(", "[", "{"):
            depth += 1
        elif is_delim(token, ")", "]", "}"):
            depth = max(0, depth - 1)
        following = code[index + 1] if index + 1 < len(code) else None
        if following is not None and following.line <= token.end_line:
            continue  # the next token is on the same line
        c_style_brace = (
            is_delim(token, "{") and len(current) > 1 and ends_value(current[-2])
            and current[0].text in PY_COMPOUND
        )
        joined = token.end_line in lex.continued_lines or (
            depth > 0 and following is not None and token.issue is None
            and not c_style_brace and _python_continues(token, following)
        )
        if following is None or not joined:
            lines.append(current)
            current, depth = [], 0
    return lines


_PY_WORD_OPERATORS = frozenset("and or not in is if else for async lambda".split())


def _python_continues(last: Token, following: Token) -> bool:
    """Inside open brackets, does the next line continue this one?

    Yes when this line clearly is not finished (it ends with an operator, a
    comma or an opening bracket) or the next line clearly is a continuation
    (it starts with a closing bracket, an operator, a comma or a dot).  Two
    strings in a row ("a" "b") are joined too.  Otherwise this line ends with
    a complete value and the next one starts a new one: the bracket was most
    likely never closed.
    """
    if last.text in OPENERS or last.text in (",", ":", ".") or last.kind is TokenKind.OPERATOR:
        return True
    if last.text in _PY_WORD_OPERATORS:
        return True
    if following.text in CLOSERS or following.text in (",", ".") or following.kind is TokenKind.OPERATOR:
        return True
    if following.text in _PY_WORD_OPERATORS:
        return True
    return last.kind is TokenKind.STRING and following.kind is TokenKind.STRING


def _split_python_line(tokens: list[Token]):
    """Split one logical line at ';' and after a compound header's ':'.

    Yields (tokens, is_header, has_colon, has_inline_body) for each piece.
    """
    pieces = []
    rest = tokens
    while rest:
        if _is_python_header(rest):
            colon = _header_colon(rest)
            if colon is None:
                pieces.append((rest, True, False, False))
                break
            body = rest[colon + 1:]
            pieces.append((rest[: colon + 1], True, True, bool(body)))
            rest = body
            continue
        semicolon = find_top(rest, ";")
        if semicolon is None:
            pieces.append((rest, False, False, False))
            break
        pieces.append((rest[: semicolon + 1], False, False, False))
        rest = rest[semicolon + 1:]
    return pieces


def _is_python_header(tokens: list[Token]) -> bool:
    first = tokens[0]
    if len(tokens) > 1 and tokens[1].text in ASSIGNMENT_OPS:
        return False                      # "class = 5" assigns to a keyword (check 6)
    if first.kind is TokenKind.KEYWORD and first.text in PY_COMPOUND:
        return True
    # "match" and "case" are soft keywords: headers only in the shape "match x:".
    if first.text in ("match", "case") and len(tokens) > 2 and tokens[-1].text == ":":
        second = tokens[1]
        return not (second.text in ASSIGNMENT_OPS or is_delim(second, ".", ",", ")", "]", ":"))
    return False


def _header_colon(tokens: list[Token]) -> int | None:
    """Index of the ':' that ends a header, skipping the ':' of a lambda."""
    open_lambdas = 0
    for index, token, depth in top_level(tokens):
        if depth:
            continue
        if token.text == "lambda":
            open_lambdas += 1
        elif is_delim(token, ":"):
            if open_lambdas:
                open_lambdas -= 1
            else:
                return index
    return None


def _classify_python(statement: Statement) -> None:
    tokens = statement.tokens
    first = tokens[0]
    if statement.header:
        keyword = tokens[1].text if first.text == "async" and len(tokens) > 1 else first.text
        statement.keyword = keyword
        statement.kind = PY_HEADER_KINDS.get(keyword, "expression")
        return
    assigns = len(tokens) > 1 and tokens[1].text in ASSIGNMENT_OPS
    if first.kind is TokenKind.KEYWORD and first.text in PY_SIMPLE_KINDS and not assigns:
        statement.keyword = first.text
        statement.kind = PY_SIMPLE_KINDS[first.text]
        return
    code = statement.code
    if is_delim(first, "@") or first.text == "@":
        statement.kind = "decorator"
    elif first.text == "type" and len(code) > 2 and code[1].kind is TokenKind.IDENTIFIER and (
        code[2].text in ("=", "[")
    ):
        statement.kind = "declaration"  # type alias (Python 3.12)
    elif find_top(code, *ASSIGNMENT_OPS) is not None:
        statement.kind = "assignment"
    elif find_top(code, ":") is not None:
        statement.kind = "declaration"  # annotated name: x: int
    else:
        statement.kind = _call_kind(code) or "expression"


def _leading_whitespace(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t\f"))]


def _width(whitespace: str, tab: int) -> int:
    """Indentation width; a tab moves to the next multiple of ``tab``, as in CPython."""
    width = 0
    for char in whitespace:
        if char == "\t":
            width = (width // tab + 1) * tab
        elif char == " ":
            width += 1
        elif char == "\f":
            width = 0
    return width


# --------------------------------------------------------------------------- C family

class _CBuilder:
    """Builds C-family statements by walking the tokens once."""

    def __init__(self, code: list[Token], lex: LexResult):
        self.code = code
        self.rules = lex.profile.rules
        self.continued = lex.continued_lines
        self.statements: list[Statement] = []
        self.current: list[Token] = []
        self.depth = 0                  # open ( and [ in the current statement
        self.blocks: list[int] = []     # indexes of headers whose '{' is still open
        self.last_closed: str | None = None   # keyword of the block closed just before
        self.enum_start = False         # the next statement lists an enum's constants

    def emit(self, ended_by: str, missing: bool = False) -> None:
        if not self.current:
            return
        statement = Statement(len(self.statements), self.current, ended_by=ended_by,
                              missing_terminator=missing)
        _classify_c(statement, self.rules)
        if self.last_closed in ("struct", "union", "enum", "class", "typedef") \
                and ended_by == ";" and statement.kind == "expression":
            statement.kind = "declaration"             # struct P { ... } p;   typedef struct { ... } T;
        if self.last_closed == "do" and statement.keyword == "while":
            statement.kind = "do_while_end"
            statement.header = False
        if self.enum_start and ended_by in (";", "}"):
            statement.kind = "enum_constants"          # enum Color { RED, GREEN, BLUE }
        self.enum_start = ended_by == "{" and statement.keyword == "enum"
        self.statements.append(statement)
        if ended_by == "{":
            self.blocks.append(statement.index)
        self.current, self.depth = [], 0
        self.last_closed = None

    def directive_end(self, index: int) -> int | None:
        """If a preprocessor line starts at ``index``, emit it and return the index after it.

        ``#include``, ``#define``, ``#pragma``, ``#region`` ... take the whole line (and the
        lines joined to it by a trailing backslash).  They are not C statements: they have
        no ';' and are left out of the expression checks.
        """
        code = self.code
        token = code[index]
        if not (self.rules.preprocessor_lines and is_delim(token, "#")):
            return None
        if index and code[index - 1].end_line >= token.line:
            return None                                  # '#' in the middle of a line
        limit = token.end_line
        while limit in self.continued:
            limit += 1
        end = index
        while end < len(code) and code[end].line <= limit:
            end += 1
        self.statements.append(Statement(len(self.statements), code[index:end],
                                         kind="preprocessor", ended_by="line"))
        return end

    def close_block(self, token: Token) -> None:
        statement = Statement(len(self.statements), [token], kind="block_end", ended_by="}")
        if self.blocks:
            opener = self.statements[self.blocks.pop()]
            statement.opener = opener.index
            opener.closer_line = token.line
            closed = opener.keyword
        else:
            closed = None
        self.statements.append(statement)
        self.last_closed = closed
        self.enum_start = False

    def run(self) -> list[Statement]:
        code = self.code
        index = 0
        while index < len(code):
            token = code[index]
            after_directive = self.directive_end(index)
            if after_directive is not None:
                index = after_directive
                continue
            current = self.current
            new_line = bool(current) and token.line > current[-1].end_line

            do_while_tail = self.last_closed == "do" and bool(current) and current[0].text == "while"
            if new_line and self.depth == 0 and current[0].text in ("case", "default") \
                    and ends_value(current[-1]) and _c_starts(code, index):
                self.emit("line")                                # a label missing its ':'
            elif new_line and self.depth == 0 and (_c_complete(current, self.rules) or (
                do_while_tail and _c_complete_header(current)
            )) and _c_starts(code, index):
                self.emit("line", missing=True)                 # a ';' is missing
            elif new_line and self.depth > 0 and ends_value(current[-1]) and _c_starts(code, index) \
                    and not _in_for_header(current):
                self.emit("line", missing=_c_complete(current, self.rules))  # a ')' is missing
            elif current and self.depth == 0 and _c_complete_header(current) \
                    and token.text not in ("{", ";") \
                    and not (current[-1].text == "else" and token.text == "if") \
                    and not (self.last_closed == "do" and current[0].text == "while"):
                if is_delim(token, ":"):                        # "if (x):" written Python-style
                    self.current.append(token)
                    self.emit(":")
                    index += 1
                    continue
                self.emit("header")                              # the body follows

            text = token.text
            if token.kind is not TokenKind.DELIMITER:
                self.current.append(token)
            elif text in ("(", "["):
                self.depth += 1
                self.current.append(token)
            elif text in (")", "]"):
                self.depth = max(0, self.depth - 1)
                self.current.append(token)
            elif text == "{":
                if (self.depth > 0 and _brace_in_expression(self.current)) or (
                    self.depth == 0 and _starts_initializer(self.current)
                ):
                    index = _append_braced(code, index, self.current)
                    continue
                self.current.append(token)
                self.emit("{")
            elif text == "}":
                if self.current:
                    self.emit("}", missing=_needs_semicolon_before_brace(self))
                self.close_block(token)
            elif text == ";":
                if self.depth > 0 and not _in_for_header(self.current):
                    self.depth = 0                               # an unclosed '(' before ';'
                self.current.append(token)
                if self.depth == 0:
                    self.emit(";")
            elif text == ":" and self.depth == 0 and len(self.current) == 1 \
                    and (self.current[0].kind is TokenKind.IDENTIFIER or (
                        self.rules.access_labels and self.current[0].text in ACCESS_LABELS)):
                self.current.append(token)                       # a label: "outer:"
                self.emit(":")
            elif text == ":" and self.depth == 0 and self.current \
                    and self.current[0].text in ("case", "default") \
                    and not any(t.text == "?" for t in self.current):
                self.current.append(token)
                self.emit(":")
            else:
                self.current.append(token)
            index += 1
        if self.current:
            self.emit("eof", missing=_c_complete(self.current, self.rules))
        return self.statements


def _c_statements(lex: LexResult) -> list[Statement]:
    return _CBuilder(_code_tokens(lex), lex).run()


def _strip_prefix(tokens: list[Token], rules: LanguageRules = DEFAULT_RULES) -> int:
    """Index of the first token after leading annotations (@Name(...)) and modifiers.

    ``rules.contextual_modifiers`` are ordinary names that act as modifiers when a type or
    keyword follows them (C#: ``async Task Run()``, ``partial class``, ``global using``).
    """
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if is_delim(token, "@") and index + 1 < len(tokens) and tokens[index + 1].text != "interface":
            index += 2
            if index < len(tokens) and is_delim(tokens[index], "("):
                index = _skip_group(tokens, index)
            continue
        if token.kind is TokenKind.KEYWORD and token.text in C_MODIFIERS:
            index += 1
            continue
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if token.kind is TokenKind.IDENTIFIER and following is not None and (
            token.text in rules.contextual_modifiers
            and following.kind in (TokenKind.IDENTIFIER, TokenKind.KEYWORD)
        ):
            index += 1
            continue
        if token.text == "<" and index > 0:          # generic method: <T> T max(...)
            end = _skip_type_arguments(tokens, index)
            if end is not None:
                index = end
                continue
        break
    return index


def _skip_group(tokens: list[Token], index: int) -> int:
    """Index just after the bracket group that opens at ``index``."""
    depth = 0
    for position in range(index, len(tokens)):
        if is_delim(tokens[position], "(", "[", "{"):
            depth += 1
        elif is_delim(tokens[position], ")", "]", "}"):
            depth -= 1
            if depth == 0:
                return position + 1
    return len(tokens)


def skip_type(tokens: list[Token], index: int) -> int | None:
    """If a type starts at ``index`` (int, String, List<String>, int[]), return the index after it.

    Also understands the C, C++ and C# spellings: ``const char *``, ``unsigned long long``,
    ``struct Point``, ``std::vector<int>``, ``string[]``, ``int?``.
    """
    while index < len(tokens) and tokens[index].kind is TokenKind.KEYWORD \
            and tokens[index].text in _TYPE_QUALIFIERS:
        index += 1
    if index >= len(tokens):
        return None
    token = tokens[index]
    keyword_type = False
    if token.text in C_PRIMITIVES or token.text == "var" or (
        token.kind is TokenKind.KEYWORD and token.text in TYPE_WORDS
    ):
        index += 1
        keyword_type = True
        while index < len(tokens) and tokens[index].kind is TokenKind.KEYWORD \
                and tokens[index].text in _BASE_TYPE_WORDS:
            index += 1                                # unsigned long long int
    elif token.kind is TokenKind.IDENTIFIER:
        index += 1
        while index + 1 < len(tokens) and is_delim(tokens[index], ".", "::") and \
                tokens[index + 1].kind is TokenKind.IDENTIFIER:
            index += 2
        if index < len(tokens) and tokens[index].text == "<":
            index = _skip_type_arguments(tokens, index)
            if index is None:
                return None
            while index + 1 < len(tokens) and is_delim(tokens[index], "::") and \
                    tokens[index + 1].kind is TokenKind.IDENTIFIER:
                index += 2
    else:
        return None
    if keyword_type:                                  # char *p, int &r, const char * const p, int?
        while index < len(tokens) and (
            tokens[index].text in ("*", "&", "&&", "?")
            or (tokens[index].kind is TokenKind.KEYWORD and tokens[index].text in ("const", "volatile"))
        ):
            index += 1
    while index + 1 < len(tokens) and is_delim(tokens[index], "[") and is_delim(tokens[index + 1], "]"):
        index += 2
    if index < len(tokens) and is_delim(tokens[index], "..."):
        index += 1
    return index


_TYPE_ARGUMENT_TOKENS = (
    frozenset("? extends super , . & [ ] :: * const typename class struct".split())
    | C_PRIMITIVES | TYPE_WORDS
)


def _skip_type_arguments(tokens: list[Token], index: int) -> int | None:
    """Skip <...> after a type name, counting '>>' and '>>>' as several closers."""
    depth = 0
    for position in range(index, len(tokens)):
        token = tokens[position]
        if token.text == "<":
            depth += 1
        elif token.text in (">", ">>", ">>>"):
            depth -= len(token.text)
            if depth <= 0:
                return position + 1 if depth == 0 else None
        elif token.kind is not TokenKind.IDENTIFIER and token.text not in _TYPE_ARGUMENT_TOKENS:
            return None
    return None


def stream_kind(tokens: list[Token]) -> str | None:
    """C++ stream chains: ``cout << a << endl`` prints, ``cin >> x`` reads, ``os << x`` writes.

    They are calls to overloaded operators, so they count as call-like statements.
    """
    index = 2 if len(tokens) > 2 and tokens[0].text == "std" and is_delim(tokens[1], "::") else 0
    if index + 1 >= len(tokens) or tokens[index].kind is not TokenKind.IDENTIFIER:
        return None
    operator = tokens[index + 1].text
    if operator not in ("<<", ">>") or find_top(tokens, *ASSIGNMENT_OPS) is not None:
        return None
    name = tokens[index].text
    if operator == "<<" and name in STREAM_OUT:
        return "output"
    return "call"


def _classify_using(statement: Statement, tokens: list[Token], start: int) -> None:
    """``using`` is a directive or alias, or (C#) a statement that disposes a resource."""
    statement.keyword = "using"
    following = tokens[start + 1] if start + 1 < len(tokens) else None
    if following is not None and is_delim(following, "("):
        statement.kind, statement.header = "context", True        # using (var f = ...) { ... }
        return
    after = skip_type(tokens, start + 1)
    if after is not None and after < len(tokens) and tokens[after].kind is TokenKind.IDENTIFIER:
        statement.kind = "declaration"                            # using var f = Open();
    else:
        statement.kind = "using"      # using System;  using static X;  using A = B;  using namespace std;


def _classify_c(statement: Statement, rules: LanguageRules = DEFAULT_RULES) -> None:
    tokens = statement.code
    if not tokens:
        statement.kind = "empty"
        return
    if len(tokens) == 1 and statement.ended_by == ":" and tokens[0].kind is TokenKind.IDENTIFIER:
        statement.kind = "label"
        return
    if tokens[0].kind is TokenKind.KEYWORD and (
        tokens[0].text == "case"
        or (tokens[0].text == "default" and (
            statement.ended_by == ":" or len(tokens) == 1 or tokens[1].text in ("->", ":")
        ))
    ):
        statement.keyword, statement.kind = tokens[0].text, "case"   # a switch label
        return
    start = _strip_prefix(tokens, rules)
    if start >= len(tokens):
        statement.kind = "annotation"
        return
    first = tokens[start]
    word = first.text
    if first.kind is TokenKind.KEYWORD and word == "using":
        _classify_using(statement, tokens, start)
        return
    if first.kind is TokenKind.KEYWORD and word == "typedef":
        statement.keyword, statement.kind = word, "declaration"
        return
    if rules.access_labels and statement.ended_by == ":" and first.text in ACCESS_LABELS \
            and len(tokens) == start + 1:
        statement.kind = "label"                                  # public:
        return
    if word in C_HEADER_KINDS and first.kind is TokenKind.KEYWORD:
        statement.keyword = word
        statement.kind = C_HEADER_KINDS[word]
        statement.header = True
        return
    if first.kind is TokenKind.KEYWORD and word in C_SIMPLE_KINDS:
        statement.keyword, statement.kind = word, C_SIMPLE_KINDS[word]
        return
    if first.kind is TokenKind.KEYWORD and word in C_TYPE_DECLARATIONS:
        statement.keyword = word
        if word == "namespace":
            statement.kind, statement.header = "namespace", statement.ended_by == "{"
        elif word in ("struct", "union", "enum") and statement.ended_by == ";":
            statement.kind = "declaration"                        # struct Point p;
        else:
            statement.kind, statement.header = "class", True
        return
    awaiting = rules.await_prefix and first.kind is TokenKind.IDENTIFIER and first.text == "await"
    after_type = None if awaiting else skip_type(tokens, start)
    if after_type is not None and after_type < len(tokens):
        following = tokens[after_type]
        if following.kind in (TokenKind.IDENTIFIER, TokenKind.INVALID) or (
            following.kind is TokenKind.KEYWORD and following.text not in VALUE_KEYWORDS
            and following.text != "instanceof"
        ):
            # "Type name ..." declares something: a method if "(" follows the name.
            nxt = tokens[after_type + 1] if after_type + 1 < len(tokens) else None
            if nxt is not None and is_delim(nxt, "(") and statement.ended_by in ("{", ";"):
                statement.kind, statement.header = "method", statement.ended_by == "{"
            else:
                statement.kind = "declaration"
            return
        if first.text in C_PRIMITIVES and following.text in ASSIGNMENT_OPS:
            statement.kind = "declaration"     # "int = 5": the name is missing
            return
    if first.kind is TokenKind.IDENTIFIER and start + 1 < len(tokens) and \
            is_delim(tokens[start + 1], "(") and statement.ended_by == "{":
        statement.kind, statement.header = "method", True   # constructor: Main(...) {
        return
    if rules.stream_chains and (stream := stream_kind(tokens)) is not None:
        statement.kind = stream
    elif find_top(tokens, *ASSIGNMENT_OPS) is not None:
        statement.kind = "assignment"
    else:
        statement.kind = _call_kind(tokens) or "expression"


def _c_complete_header(tokens: list[Token]) -> bool:
    """True for a finished control header with no body yet: 'if (x)', 'else', 'do'."""
    start = 1 if tokens[0].text == "else" and len(tokens) > 1 and tokens[1].text == "if" else 0
    keyword = tokens[start].text
    if len(tokens) == start + 1 and keyword in C_BARE_HEADERS:
        return True
    if keyword in C_PAREN_HEADERS and tokens[start].kind is TokenKind.KEYWORD \
            and len(tokens) > start + 1 and is_delim(tokens[start + 1], "("):
        return _skip_group(tokens, start + 1) == len(tokens)
    return False


def _c_complete(tokens: list[Token], rules: LanguageRules = DEFAULT_RULES) -> bool:
    """Does ``tokens`` form a finished simple statement that only lacks its ';'?"""
    if not tokens or not ends_value(tokens[-1]) or _c_complete_header(tokens):
        return False
    if tokens[0].text in ("case", "default"):
        return False
    start = _strip_prefix(tokens, rules)
    if start >= len(tokens):
        return False                      # only annotations, e.g. "@Override"
    if tokens[start].text in C_TYPE_DECLARATIONS:
        return False                      # "public class A" waits for '{'
    after_type = skip_type(tokens, start)
    if after_type is not None and after_type + 1 < len(tokens) and \
            tokens[after_type].kind is TokenKind.IDENTIFIER and is_delim(tokens[after_type + 1], "(") \
            and tokens[-1].text == ")" and _skip_group(tokens, after_type + 1) == len(tokens):
        return False                      # "void run()" waits for '{'
    if tokens[0].kind is TokenKind.IDENTIFIER and len(tokens) > 1 and is_delim(tokens[1], "(") \
            and start > 0:
        return False                      # "public Main()" constructor header
    return True


def _c_starts(code: list[Token], index: int) -> bool:
    """Does the token at ``index`` begin a new statement (not continue the last one)?"""
    token = code[index]
    following = code[index + 1] if index + 1 < len(code) else None
    if token.kind is TokenKind.KEYWORD and token.text in C_STATEMENT_STARTERS:
        return True
    if is_delim(token, "@", "}"):
        return True
    if token.kind is TokenKind.IDENTIFIER and following is not None and following.line == token.line:
        if following.kind is TokenKind.IDENTIFIER:
            return True                   # "String name"
        return following.text in ASSIGNMENT_OPS or following.text in ("(", ".", "[", "++", "--", "<")
    return False


def _in_for_header(tokens: list[Token]) -> bool:
    start = 2 if len(tokens) > 1 and tokens[0].text == "else" else 0
    return len(tokens) > start + 1 and tokens[start].text == "for" and is_delim(tokens[start + 1], "(")


def _brace_in_expression(tokens: list[Token]) -> bool:
    """A '{' inside parentheses: lambda body, anonymous class or array initializer.

    "f(x -> {", "f(new Task() {", "f(new int[] {" and "f({" are expressions.
    In "if (x > 5 {" the '{' follows a plain value, so the '(' was never closed.
    """
    if not tokens:
        return False
    last = tokens[-1].text
    if last in ("->", ",", "(", "="):
        return True
    if last in (")", "]"):
        recent = tokens[-12:]
        return any(token.text == "new" for token in recent)
    return False


def _starts_initializer(tokens: list[Token]) -> bool:
    """A '{' that belongs to an expression: int[] a = {1, 2};  Runnable r = () -> {...};"""
    if not tokens:
        return False
    if tokens[-1].text in ("=", "->"):
        return True
    has_assignment = find_top(tokens, *ASSIGNMENT_OPS) is not None
    if has_assignment and any(t.text == "new" for t in tokens) and (
        tokens[-1].kind is TokenKind.IDENTIFIER or tokens[-1].text == ">"
    ):
        return True                       # C#: new List<int> { 1, 2 }   new Point { X = 1 }
    return (has_assignment or tokens[0].text in ("return", "yield")) and tokens[-1].text in (")", "]")


def _append_braced(code: list[Token], index: int, current: list[Token]) -> int:
    """Append a { ... } that is part of an expression; return the index after it.

    An array initializer cannot contain ';', so for one the scan also stops at a
    ';' (the missing '}' is then reported by the bracket check).
    """
    array_like = bool(current) and current[-1].text in ("=", "]", ",", "(")
    depth = 0
    while index < len(code):
        token = code[index]
        if array_like and depth > 0 and is_delim(token, ";"):
            return index
        if array_like and depth == 1 and is_delim(token, "}"):
            following = code[index + 1] if index + 1 < len(code) else None
            if following is not None and following.text not in (";", ",", ")", "}", "."):
                return index          # this '}' closes a block, not the initializer
            if following is not None and following.text == "}" and following.line > token.line:
                return index
        current.append(token)
        index += 1
        if is_delim(token, "{"):
            depth += 1
        elif is_delim(token, "}"):
            depth -= 1
            if depth == 0:
                return index
    return index


def _needs_semicolon_before_brace(builder: _CBuilder) -> bool:
    tokens = builder.current
    if _c_complete_header(tokens) or not _c_complete(tokens, builder.rules):
        return False
    if builder.blocks:  # enum constants need no ';' before the '}'
        enclosing = builder.statements[builder.blocks[-1]]
        if enclosing.keyword == "enum":
            return False
    return True
