"""Check 5: control structure headers (and function / class headers).

Each kind of header has a small grammar, written here in EBNF:

Python::

    if_header    = ("if" | "elif" | "while") condition ":"
    else_header  = "else" ":"
    for_header   = "for" targets "in" iterable ":"
    def_header   = "def" NAME "(" [parameters] ")" ["->" type] ":"
    class_header = "class" NAME ["(" bases ")"] ":"

Java (C family)::

    if_header    = ("if" | "while" | "switch") "(" condition ")"
    for_header   = "for" "(" [init] ";" [condition] ";" [update] ")"
                 | "for" "(" type NAME ":" collection ")"
    case_label   = "case" value ":" | "default" ":"

A header that does not fit its grammar is reported here.  The ':' and ';'
terminators are check 3's job, and the expressions inside a header are
check 4's.
"""

from __future__ import annotations

from ..diagnostics import Check, Diagnostic, at
from ..structure import Statement, find_top, is_delim, skip_type, split_top
from ..tokens import Token, TokenKind
from . import Context

HEADER = "Invalid Control Structure Header"


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for statement in context.statements:
        report = _Reporter(statement, diagnostics)
        if context.python:
            if statement.header:
                _python_header(statement, report)
        else:
            _c_statement(statement, report)
    return diagnostics


class _Reporter:
    def __init__(self, statement: Statement, diagnostics: list[Diagnostic]):
        self.statement = statement
        self.diagnostics = diagnostics

    def __call__(self, token: Token, code: str, message: str, hint: str,
                 category: str = HEADER) -> None:
        self.diagnostics.append(at(token, Check.CONTROL, code, category, message,
                                   hint=hint, statement=self.statement.index))


# ----------------------------------------------------------------- Python

def _python_header(statement: Statement, report: _Reporter) -> None:
    code = statement.code
    keyword = statement.keyword
    body = code[2:] if code[0].text == "async" else code[1:]
    if body and is_delim(body[-1], "{"):
        body = body[:-1]                    # "if x > 5 {" is reported as a missing ':'
    first = code[0]

    if keyword in ("if", "elif", "while"):
        if not body:
            report(first, "E501", f"Missing condition in '{keyword}' statement.",
                   f"Write a condition before ':', e.g. {keyword} x > 0:")
            return
        equals = find_top(body, "=")
        if equals is not None:
            report(body[equals], "E505", "Assignment '=' cannot be used as a condition.",
                   "Use '==' to compare two values.")
    elif keyword == "else":
        if body and body[0].text == "if":
            report(body[0], "E504", "'else if' is not valid in Python.",
                   "Use 'elif condition:' instead.")
        elif body:
            report(body[0], "E504", "'else' does not take a condition.",
                   "Use 'elif condition:' to test another condition, or remove the condition.")
    elif keyword in ("try", "finally") and body:
        report(body[0], "E504", f"'{keyword}' does not take an expression.",
               f"Write just '{keyword}:'.")
    elif keyword == "for":
        _python_for(first, body, report)
    elif keyword == "def":
        _python_def(first, body, report)
    elif keyword == "class" and (not body or body[0].kind not in (
        TokenKind.IDENTIFIER, TokenKind.INVALID, TokenKind.KEYWORD
    )):
        report(first, "E506", "Class definition is missing a name.",
               "Write: class Name:", category="Invalid Class Header")
    elif keyword in ("with", "match") and not body:
        report(first, "E501", f"Missing expression after '{keyword}'.",
               f"Write: {keyword} something:")


def _python_for(first: Token, body: list[Token], report: _Reporter) -> None:
    position = find_top(body, "in")
    if position is None:
        report(first, "E503", "'for' loop header is missing the keyword 'in'.",
               "Write: for item in collection:")
    elif position == 0:
        report(body[0], "E503", "Missing loop variable between 'for' and 'in'.",
               "Write: for item in collection:")
    elif position == len(body) - 1:
        report(body[position], "E503", "Missing the collection to loop over after 'in'.",
               "Write: for item in collection:")


def _python_def(first: Token, body: list[Token], report: _Reporter) -> None:
    category = "Invalid Function Header"
    if not body or body[0].kind not in (TokenKind.IDENTIFIER, TokenKind.INVALID, TokenKind.KEYWORD):
        report(first, "E506", "Function definition is missing a name.",
               "Write: def name(parameters):", category=category)
        return
    if len(body) < 2 or not is_delim(body[1], "("):
        report(body[0], "E506", f"Missing parentheses after the function name '{body[0].text}'.",
               f"Write: def {body[0].text}():", category=category)
        return
    end = _group_end(body, 1)
    inner = body[2: end - 1] if is_delim(body[end - 1], ")") else body[2:end]
    seen_default = after_star = False
    for parameter in split_top(inner, ","):
        if not parameter:
            continue
        if parameter[0].text in ("*", "**", "/"):
            after_star = after_star or parameter[0].text in ("*", "**")
            continue
        name = parameter[0]
        if len(parameter) > 1 and not (is_delim(parameter[1], ":") or parameter[1].text == "="):
            report(parameter[1], "E509",
                   f"Missing ',' between parameters '{name.text}' and '{parameter[1].text}'.",
                   "Separate parameters with commas.", category=category)
            return
        has_default = find_top(parameter, "=") is not None
        if seen_default and not has_default and not after_star:
            report(name, "E510",
                   f"Parameter '{name.text}' without a default value follows a parameter "
                   "with a default value.",
                   "Move parameters with default values to the end.", category=category)
            return
        seen_default = seen_default or has_default


# --------------------------------------------------------------- C family

def _c_statement(statement: Statement, report: _Reporter) -> None:
    code = statement.code
    if not code:
        return
    first = code[0]
    if first.kind is TokenKind.IDENTIFIER and first.text in ("elif", "elsif", "elseif"):
        report(first, "E504", f"'{first.text}' is not a keyword in this language.",
               "Use 'else if (condition)'.")
        return
    if statement.kind == "case":
        if statement.ended_by != ":" and find_top(code, "->") is None:
            report(statement.last, "E507", f"The '{first.text}' label must end with ':'.",
                   f"Write: {first.text} value:" if first.text == "case" else "Write: default:")
        return
    if not (statement.header or statement.kind == "do_while_end"):
        if statement.kind == "method":
            _c_method(statement, report)
        return

    start = 0
    if first.text == "else":
        if len(code) > 1 and code[1].text == "if":
            start = 1
        elif len(code) > 1:
            report(code[1], "E504", "'else' does not take a condition.",
                   "Use 'else if (condition)' to test another condition.")
            return
        else:
            return
    keyword = code[start].text
    if keyword in ("if", "while", "switch", "synchronized", "catch"):
        _c_parenthesized(statement, code, start, keyword, report)
    elif keyword == "for":
        _c_for(statement, code, start, report)
    elif statement.kind == "method":
        _c_method(statement, report)


def _c_parenthesized(statement: Statement, code: list[Token], start: int, keyword: str,
                     report: _Reporter) -> None:
    keyword_token = code[start]
    if start + 1 >= len(code) or not is_delim(code[start + 1], "("):
        report(keyword_token, "E502", f"The condition after '{keyword}' must be in parentheses.",
               f"Write: {keyword} (condition) {{ ... }}")
        return
    end = _group_end(code, start + 1)
    inner = code[start + 2: end - 1]
    if not inner and keyword != "catch":
        report(keyword_token, "E501", f"Missing condition inside '{keyword} ( )'.",
               f"Write a condition between the parentheses: {keyword} (x > 0)")
    elif keyword in ("if", "while") and find_top(inner, "=") is not None:
        report(inner[find_top(inner, "=")], "W505",
               "Assignment '=' inside the condition. Did you mean '=='?",
               "Use '==' to compare two values.")
    _c_after_header(statement, keyword, report)


def _c_for(statement: Statement, code: list[Token], start: int, report: _Reporter) -> None:
    keyword = code[start]
    if start + 1 >= len(code) or not is_delim(code[start + 1], "("):
        report(keyword, "E502", "The 'for' header must be in parentheses.",
               "Write: for (int i = 0; i < n; i++) { ... }")
        return
    end = _group_end(code, start + 1)
    inner = code[start + 2: end - 1]
    separators = len(split_top(inner, ";")) - 1
    if separators == 2 or (separators == 0 and find_top(inner, ":") is not None):
        _c_after_header(statement, "for", report)
        return
    hint = "Write: for (int i = 0; i < n; i++)"
    if find_top(inner, ",") is not None:
        hint = "Use ';' instead of ',' between the three parts: for (int i = 0; i < n; i++)"
    report(keyword, "E503",
           f"A 'for' header needs two ';' separators (init; condition; update), found {separators}.",
           hint)


def _c_after_header(statement: Statement, keyword: str, report: _Reporter) -> None:
    if statement.ended_by == ":":
        report(statement.last, "E508", f"Unexpected ':' after the '{keyword}' header.",
               "This language marks blocks with { }, not ':'.")
    elif statement.ended_by == ";" and keyword in ("if", "while", "for") \
            and statement.kind != "do_while_end":
        report(statement.last, "W509",
               f"Empty statement: the ';' right after the '{keyword}' header ends it, so the "
               "code below runs no matter what.", "Remove the ';' after the header.")


def _c_method(statement: Statement, report: _Reporter) -> None:
    """Every parameter needs a type and a name: void greet(String name, int times)."""
    code = statement.code
    position = find_top(code, "(")
    if position is None:
        return
    end = _group_end(code, position)
    inner = code[position + 1: end - 1]
    for parameter in split_top(inner, ","):
        while parameter and (parameter[0].text == "final" or is_delim(parameter[0], "@")):
            parameter = parameter[2:] if is_delim(parameter[0], "@") else parameter[1:]
        if not parameter:
            continue
        after_type = skip_type(parameter, 0)
        if after_type is None or after_type >= len(parameter):
            report(parameter[0], "E506",
                   f"Parameter '{_text(parameter)}' needs both a type and a name.",
                   "Write each parameter as: Type name (for example: int count).",
                   category="Invalid Method Header")
            return


def _group_end(tokens: list[Token], start: int) -> int:
    depth = 0
    for index in range(start, len(tokens)):
        if is_delim(tokens[index], "(", "[", "{"):
            depth += 1
        elif is_delim(tokens[index], ")", "]", "}"):
            depth -= 1
            if depth == 0:
                return index + 1
    return len(tokens)


def _text(tokens: list[Token]) -> str:
    return " ".join(token.text for token in tokens)
