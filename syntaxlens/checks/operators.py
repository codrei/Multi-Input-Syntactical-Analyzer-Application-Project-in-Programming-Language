"""Check 4: operator syntax.

This module decides *which parts* of each statement are expressions: the value
of an assignment, the condition of an ``if``, the arguments of a call, and so on.
It then hands each part to the two-state machine in expressions.py, which finds
consecutive operators (``+ *``), missing operands (``x = 5 +``) and missing
operators (``x = 5 6``).  It also checks that the left side of ``=`` can be
assigned to (``5 = x`` cannot).
"""

from __future__ import annotations

from ..diagnostics import Diagnostic
from ..expressions import ExpressionChecker, assignment_problem
from ..structure import ASSIGNMENT_OPS, C_MODIFIERS, Statement, find_top, is_delim, skip_type, split_top
from ..tokens import Token, TokenKind
from . import Context
from .identifiers import broken_name


def check(context: Context) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for statement in context.statements:
        checker = ExpressionChecker(context.profile, statement.index)
        if context.python:
            _python_statement(statement, checker)
        else:
            _c_statement(statement, checker, context.profile.key)
        diagnostics += checker.diagnostics
    return diagnostics


# ----------------------------------------------------------------- Python

def _python_statement(statement: Statement, checker: ExpressionChecker) -> None:
    code = statement.code
    if code and code[-1].text == ";":
        code = code[:-1]
    if not code:
        return
    kind, keyword = statement.kind, statement.keyword
    body = code[2:] if code[0].text == "async" else code[1:]
    if statement.header and body and is_delim(body[-1], "{"):
        body = body[:-1]                         # "if x > 5 {" is reported as a missing ':'

    if statement.header:
        if keyword in ("if", "elif", "while", "match"):
            checker.expression(body)
        elif keyword == "for":
            position = find_top(body, "in")
            if position is not None:
                checker.expression_list(body[:position], star=True)
                checker.expression_list(body[position + 1:], star=True)
        elif keyword in ("with", "except"):
            for item in split_top(body, ","):
                position = find_top(item, "as")
                checker.expression(item if position is None else item[:position])
        elif keyword == "class" and len(body) > 1 and is_delim(body[1], "("):
            checker.expression(body)                 # the base classes look like a call
        return
    if kind in ("return", "delete"):
        checker.expression_list(body, star=True)
    elif kind == "exception" and keyword == "raise":
        position = find_top(body, "from")
        checker.expression(body if position is None else body[:position])
    elif kind == "assert":
        checker.expression_list(body)
    elif kind == "decorator":
        checker.expression(body)
    elif kind in ("assignment", "declaration"):
        _python_assignment(code, checker)
    elif kind in ("expression", "call", "output"):
        checker.expression_list(code, star=True)


def _python_assignment(code: list[Token], checker: ExpressionChecker) -> None:
    """x = 1, a = b = 0, x += 1, a, *rest = items, x: int = 5, type T = int"""
    if code[0].text == "type" and len(code) > 2 and code[1].kind is TokenKind.IDENTIFIER:
        position = find_top(code, "=")
        if position is not None:
            checker.expression(code[position + 1:])
        return
    positions = [index for index, token, depth in _top(code)
                 if depth == 0 and token.kind is TokenKind.OPERATOR and token.text in ASSIGNMENT_OPS]
    if not positions:                                 # annotation only: "x: int"
        colon = find_top(code, ":")
        checker.expression(code[colon + 1:] if colon is not None else code)
        return
    targets, start = [], 0
    for position in positions:
        targets.append((code[start:position], code[position]))
        start = position + 1
    value = code[start:]
    for target, operator in targets:
        colon = find_top(target, ":")
        if colon is not None:                         # annotated: "x: int = 5"
            checker.expression(target[colon + 1:])
            target = target[:colon]
        if not target:
            checker.report(operator, "E405", "Missing Operand",
                           f"Missing variable name before '{operator.text}'.",
                           hint="Write the variable to assign to, e.g. total = 5.")
            continue
        if target[-1].kind is TokenKind.OPERATOR:      # "a == = b": two operators in a row
            checker.report_consecutive(target[-1], operator)
            continue
        problem = assignment_problem(target, python=True)
        if problem is None:
            if not broken_name(target):              # a broken name is check 6's error
                checker.expression_list(target, star=True)
        else:
            what, culprit = problem
            checker.report(culprit, "E404", "Invalid Assignment Target",
                           f"Cannot assign to {what} '{_text(target)}'. Only a variable, "
                           f"attribute or list element can be on the left of '{operator.text}'.",
                           hint="Put a variable name on the left side, e.g. total = 5.")
    if not value:
        operator = targets[-1][1]
        checker.report(operator, "E402", "Missing Operand",
                       f"Missing value after '{operator.text}'.",
                       hint=f"Write the value to assign after '{operator.text}'.")
    else:
        checker.expression_list(value, star=True)


# --------------------------------------------------------------- C family

def _c_statement(statement: Statement, checker: ExpressionChecker, lang: str = "java") -> None:
    code = statement.code
    if code and code[-1].text == ";":
        code = code[:-1]
    if not code or statement.kind in ("method", "class", "import", "package", "annotation",
                                       "block_end", "label", "empty", "enum_constants",
                                       "preprocessor", "using", "namespace"):
        return
    kind = statement.kind
    start = 1
    if code[0].text == "else":
        start = 2 if len(code) > 1 and code[1].text == "if" else 1
    keyword = code[start - 1].text if statement.header or kind == "do_while_end" else None

    if keyword in ("if", "while", "switch", "synchronized"):
        _first_group(code, start, checker.expression)
    elif keyword == "for":
        _first_group(code, start, lambda inner: _for_header(inner, checker))
    elif kind == "case":
        if statement.ended_by != ":" and find_top(code, "->") is None:
            return                                   # malformed label: check 5 reports it
        body = code[1:]
        arrow = find_top(body, "->")
        if arrow is not None:
            checker.expression_list(body[:arrow])
            checker.expression(body[arrow + 1:])
        else:
            checker.expression_list(body)
    elif kind in ("return", "exception") and code[0].text in ("return", "throw", "yield"):
        if len(code) > 1:
            checker.expression(code[1:])
    elif kind == "assert":
        for part in split_top(code[1:], ":"):
            checker.expression(part)
    elif kind == "declaration":
        _declaration(code, checker)
    elif kind in ("assignment", "expression", "call", "output"):
        checker.expression(code)
        if kind == "expression" and not checker.diagnostics:
            if lang == "java":
                _not_a_statement(code, checker)
            elif lang == "csharp":
                _csharp_not_a_statement(code, checker)
            else:
                _unused_value(code, checker, lang)


def _first_group(code: list[Token], start: int, handle) -> None:
    """Pass the inside of the parentheses after a keyword to ``handle``."""
    if start < len(code) and is_delim(code[start], "("):
        end = ExpressionChecker.group_end(code, start)
        inner = code[start + 1: end - 1] if is_delim(code[end - 1], ")") else code[start + 1: end]
        if inner:
            handle(inner)


def _for_header(inner: list[Token], checker: ExpressionChecker) -> None:
    parts = split_top(inner, ";")
    if len(parts) == 3:                               # for (init; condition; update)
        init, condition, update = parts
        if init:
            if skip_type(init, 0) is not None and skip_type(init, 0) < len(init) and \
                    init[skip_type(init, 0)].kind is TokenKind.IDENTIFIER:
                _declaration(init, checker)
            else:
                checker.expression_list(init)
        if condition:
            checker.expression(condition)
        if update:
            checker.expression_list(update)
    elif len(parts) == 1:
        colon = find_top(inner, ":")
        if colon is not None:                         # for (Type item : collection)
            checker.expression(inner[colon + 1:])


def _declaration(code: list[Token], checker: ExpressionChecker) -> None:
    """int a = 1, b = a + 2;  String[] names = {"x", "y"};"""
    index = 0
    while index < len(code) and (code[index].text in ("final", "static", "public", "private",
                                                       "protected", "transient", "volatile")):
        index += 1
    after_type = skip_type(code, index)
    if after_type is None:
        return
    for declarator in split_top(code[after_type:], ","):
        position = find_top(declarator, "=")
        if position is None:
            continue
        value = declarator[position + 1:]
        if not value:
            checker.report(declarator[position], "E402", "Missing Operand",
                           "Missing value after '='.", hint="Write the initial value after '='.")
        else:
            checker.expression(value)


def _not_a_statement(code: list[Token], checker: ExpressionChecker) -> None:
    """Java rejects expressions whose value is thrown away, such as 'x + 1;'.

    Allowed on their own are assignments, calls, ++/-- and 'new' objects.
    """
    if code[-1].text in ("++", "--") or code[0].text in ("++", "--", "new", "this", "super"):
        return
    if code[-1].text == ")" and not any(token.kind is TokenKind.OPERATOR and
                                        token.text not in ("->",) for _, token, depth in _top(code)
                                        if depth == 0):
        return                                        # a method call
    if any(token.text == "->" for token in code):
        return
    checker.report(code[0], "E406", "Invalid Expression Statement",
                   f"'{_text(code)}' is not a statement: its value would be computed and thrown away.",
                   hint="Assign the result to a variable or use it in a call, e.g. x = x + 1;")


def _is_call(code: list[Token], ignore: tuple[str, ...] = ("->",)) -> bool:
    """A name or member access followed by '(...)': no operator outside the brackets."""
    return code[-1].text == ")" and not any(
        token.kind is TokenKind.OPERATOR and token.text not in ignore
        for _, token, depth in _top(code) if depth == 0
    )


def _strip_generics(code: list[Token]) -> list[Token]:
    """Remove type arguments, so that ``Run<int>(x)`` is read as ``Run(x)``."""
    result: list[Token] = []
    index = 0
    while index < len(code):
        token = code[index]
        if token.text == "<" and result and result[-1].kind is TokenKind.IDENTIFIER:
            end = skip_type(code, index - 1)
            if end is not None and end > index and end < len(code) + 1 and \
                    code[end - 1].text in (">", ">>", ">>>"):
                index = end
                continue
        result.append(token)
        index += 1
    return result


_ACCESSORS = frozenset("get set init add remove".split())


def _csharp_not_a_statement(code: list[Token], checker: ExpressionChecker) -> None:
    """C# allows only these expressions as statements: assignment, call, ``x++`` / ``--x``,
    ``await``, and object creation with ``new``.  ``x + 1;`` is error CS0201."""
    code = _strip_generics(code)
    first, last = code[0], code[-1]
    if first.kind is TokenKind.IDENTIFIER and first.text == "await" and len(code) > 1:
        return                                        # await task;
    if last.text in ("++", "--") or first.text in ("++", "--", "new"):
        return
    body = [token for token in code if not (token.kind is TokenKind.KEYWORD
                                             and token.text in C_MODIFIERS)]
    if body and body[0].text in _ACCESSORS and (len(body) == 1 or body[1].text == "=>"):
        return                                        # property accessor: get; set; init;
    if _is_call(code, ignore=("->", "?.", "!")):
        return                                        # Foo(); a?.Foo(); a!.Foo();
    checker.report(first, "E406", "Invalid Expression Statement",
                   f"'{_text(code)}' is not a statement: its value would be computed and thrown away.",
                   hint="Assign the result to a variable or use it in a call, e.g. x = x + 1;")


_UNUSED_OPERATORS = frozenset("+ - / % == != < > <= >= | ^ << >>".split())


def _unused_value(code: list[Token], checker: ExpressionChecker, lang: str) -> None:
    """C and C++ accept any expression as a statement, so a discarded value is only a warning.

    Calls, ``++``, ``cond ? f() : g();``, ``ok && f();``, ``(void)x;``, macro names and C++ stream
    chains (``cout << a``) are common and valid, so nothing is said about them.
    """
    code = _strip_generics(code) if lang == "cpp" else code
    if len(code) >= 3 and code[0].text == "(" and code[1].text == "void" and code[2].text == ")":
        return
    operators = [token for index, token, depth in _top(code)
                 if depth == 0 and index > 0 and token.kind is TokenKind.OPERATOR]
    literal = len(code) == 1 and code[0].kind in (TokenKind.NUMBER, TokenKind.STRING, TokenKind.CHAR)
    if not literal:
        texts = {token.text for token in operators}
        if not texts & _UNUSED_OPERATORS or texts & {"?", "&&", "||", "++", "--"}:
            return
        if lang == "cpp" and texts & {"<<", ">>"}:
            return                                    # a stream chain
    checker.report(code[0], "W406", "Unused Expression Value",
                   f"'{_text(code)}' computes a value that is never used.",
                   hint="Assign the result to a variable, use it in a call, or remove the statement.")


# ----------------------------------------------------------------- helpers

def _top(tokens: list[Token]):
    depth = 0
    for index, token in enumerate(tokens):
        if is_delim(token, ")", "]", "}"):
            depth -= 1
        yield index, token, depth
        if is_delim(token, "(", "[", "{"):
            depth += 1


def _text(tokens: list[Token]) -> str:
    return " ".join(token.text for token in tokens)

