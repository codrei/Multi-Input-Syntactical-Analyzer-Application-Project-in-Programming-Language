"""Expression checking: the engine behind check 4 (operator syntax).

An expression alternates between values (operands) and operators::

    y = 20 + * 5
        ^^ ^ ^ ^
        |  | | '-- value
        |  | '---- operator  <-- but a value was expected here!
        |  '------ operator
        '--------- value

So the checker is a machine with two states:

* **EXPECT_OPERAND** (a value is needed): a name, number or string moves to
  EXPECT_OPERATOR.  An operator that can also be a *sign* (``-5``, ``+5``,
  ``not x``, ``!x``) is accepted and the machine keeps waiting for the value.
  Any other operator here is an error: ``+ *`` means two binary operators with
  no value between them.
* **EXPECT_OPERATOR** (a value was just read): a binary operator moves back to
  EXPECT_OPERAND.  ``(`` starts a call, ``[`` an index, ``.`` an attribute.
  Another plain value here is an error: ``x = 5 6`` is missing an operator.

If the expression ends while a value is still expected (``x = 5 +``), the
right-hand operand is missing.  Brackets are checked recursively: the inside
of ``( )``, ``[ ]`` and ``{ }`` is a list of expressions separated by commas.
"""

from __future__ import annotations

import difflib

from .diagnostics import Check, Diagnostic, at
from .profiles.base import LanguageProfile
from .structure import (
    ASSIGNMENT_OPS,
    C_PRIMITIVES,
    OPENERS,
    VALUE_KEYWORDS,
    is_delim,
    skip_type,
)
from .tokens import Token, TokenKind

EXPECT_OPERAND = "operand"
EXPECT_OPERATOR = "operator"

PY_BINARY = frozenset(
    "+ - * / // % ** @ << >> & | ^ < > <= >= == != := and or in is if else for".split()
) | ASSIGNMENT_OPS
PY_PREFIX = frozenset("+ - ~ not await".split())
C_BINARY = frozenset(
    "+ - * / % << >> >>> < > <= >= == != & | ^ && || ? : -> instanceof".split()
) | ASSIGNMENT_OPS
C_PREFIX = frozenset("+ - ! ~ ++ --".split())
C_POSTFIX = frozenset("++ --".split())

# Hints for operator pairs that are habits from other languages.
_PAIR_HINTS = {
    ("&", "&"): "Python writes logical AND as 'and', not '&&'.",
    ("|", "|"): "Python writes logical OR as 'or', not '||'.",
    ("==", "="): "There is no '===' operator here; use '=='.",
    ("=", "<"): "Did you mean '<=' (less than or equal)?",
    ("=", ">"): "Did you mean '>=' (greater than or equal)?",
}


class ExpressionChecker:
    """Checks expressions of one statement and collects the problems found."""

    def __init__(self, profile: LanguageProfile, statement: int):
        self.profile = profile
        self.python = profile.family == "python"
        self.statement = statement
        self.binary = PY_BINARY if self.python else C_BINARY
        self.prefix = PY_PREFIX if self.python else C_PREFIX
        self.diagnostics: list[Diagnostic] = []

    # ------------------------------------------------------------- public API

    def expression_list(self, tokens: list[Token], *, star: bool = False) -> None:
        """Check comma-separated expressions such as ``a, b + 1, *rest``."""
        for element in self.split_elements(tokens):
            if element:
                self.expression(element, star=star)

    def expression(self, tokens: list[Token], *, star: bool = False) -> None:
        """Check one expression with the two-state machine described above."""
        state = EXPECT_OPERAND
        last_operator: Token | None = None   # binary operator still waiting for its value
        last_prefix: Token | None = None     # sign operator still waiting for its value
        segment_start = 0                    # where the current assignment target begins (C)
        index = 0
        while index < len(tokens):
            token = tokens[index]
            text = token.text

            if state == EXPECT_OPERAND:
                if self.is_await(tokens, index):
                    last_prefix = token                   # C#: await Foo()
                    index += 1
                elif self.is_operand(token):
                    state, last_operator, last_prefix = EXPECT_OPERATOR, None, None
                    index += 1
                elif is_delim(token, *OPENERS):
                    end = self.group_end(tokens, index)
                    if not self.python and text == "(" and self.is_cast(tokens, index, end):
                        index = end                       # (int) x: a cast, the value follows
                        continue
                    if text == "{" and last_operator is not None and last_operator.text == "->":
                        pass                              # lambda body: statements, not checked here
                    else:
                        self.group(tokens, index, end, after_value=False)
                    state, last_operator, last_prefix = EXPECT_OPERATOR, None, None
                    index = end
                elif self.python and text == "lambda":
                    index = self.skip_lambda(tokens, index)
                elif self.python and text in ("*", "**") and star and index == 0:
                    index += 1                            # *args / **kwargs, only at an item's start
                elif self.python and text == "yield":
                    index += 2 if index + 1 < len(tokens) and tokens[index + 1].text == "from" else 1
                elif not self.python and text == "new":
                    index = self.skip_new(tokens, index)
                    state, last_operator, last_prefix = EXPECT_OPERATOR, None, None
                elif text in self.prefix and token.kind in (TokenKind.OPERATOR, TokenKind.KEYWORD):
                    last_prefix = token
                    index += 1
                elif text in self.binary and token.kind in (TokenKind.OPERATOR, TokenKind.KEYWORD):
                    if last_operator is not None:
                        self.report_consecutive(last_operator, token)
                    else:
                        self.report(token, "E405", "Missing Operand",
                                    f"Missing left operand before '{text}'.",
                                    hint=f"Put a value before '{text}'.")
                    last_operator = token
                    index += 1
                else:
                    return                                # not an expression we understand
            else:  # EXPECT_OPERATOR
                if is_delim(token, "(", "["):
                    end = self.group_end(tokens, index)
                    self.group(tokens, index, end, after_value=True)
                    index = end
                elif is_delim(token, ".", "::") or text == "?.":
                    following = tokens[index + 1] if index + 1 < len(tokens) else None
                    if following is not None and (
                        following.kind in (TokenKind.IDENTIFIER, TokenKind.KEYWORD)
                        or following.text == "<"
                    ):
                        index += 2
                    else:
                        self.report(token, "E408", "Missing Member Name",
                                    f"Expected a name after '{text}'.",
                                    hint=f"Write the attribute or method name after '{text}'.")
                        return
                elif not self.python and text in C_POSTFIX:
                    index += 1                            # i++
                elif self.python and text == "not" and index + 1 < len(tokens) \
                        and tokens[index + 1].text == "in":
                    state, last_operator = EXPECT_OPERAND, token
                    index += 2                            # "not in"
                elif not self.python and text == "instanceof":
                    index = self.skip_instanceof(tokens, index)
                elif text in self.binary and token.kind in (TokenKind.OPERATOR, TokenKind.KEYWORD):
                    if not self.python and text in ASSIGNMENT_OPS:
                        self.check_target(tokens[segment_start:index], token)
                        segment_start = index + 1
                    state, last_operator = EXPECT_OPERAND, token
                    index += 1
                elif self.is_operand(token) or is_delim(token, "{"):
                    previous = tokens[index - 1]
                    if not (self.python and previous.kind is TokenKind.STRING
                            and token.kind is TokenKind.STRING):  # "a" "b" is valid Python
                        self.report_missing_operator(previous, token, tokens)
                        return
                    index += 1
                else:
                    return
        if state == EXPECT_OPERAND and tokens:
            waiting = last_operator or last_prefix
            if waiting is not None:
                self.report_missing_operand(waiting, tokens)

    def is_await(self, tokens: list[Token], index: int) -> bool:
        """C# ``await`` is an ordinary name that acts as a prefix when a value follows it."""
        token = tokens[index]
        if self.profile.key != "csharp" or token.kind is not TokenKind.IDENTIFIER \
                or token.text != "await" or index + 1 >= len(tokens):
            return False
        following = tokens[index + 1]
        return following.kind in (TokenKind.IDENTIFIER, TokenKind.KEYWORD, TokenKind.NUMBER,
                                  TokenKind.STRING, TokenKind.CHAR) or is_delim(following, "(")

    # -------------------------------------------------------------- brackets

    def group(self, tokens: list[Token], start: int, end: int, *, after_value: bool) -> None:
        """Check the inside of the bracket group opening at ``start``."""
        opener = tokens[start].text
        close = end - 1 if end - 1 > start and tokens[end - 1].text == OPENERS[opener] else end
        inner = tokens[start + 1: close]
        if opener == "[" and after_value:              # indexing / slicing: a[1], a[1:3], a[::2]
            for part in self.split_top(inner, ":"):
                self.expression_list(part)
            return
        elements = self.split_elements(inner)
        for position, element in enumerate(elements):
            if element:
                if self.python and opener == "(" and after_value and len(element) > 2 \
                        and element[0].kind is TokenKind.IDENTIFIER and element[1].text == "=":
                    element = element[2:]               # keyword argument: name=value
                if self.python and opener == "{":       # dict entries: key: value
                    for part in self.split_top(element, ":"):
                        if part:
                            self.expression(part, star=True)
                    continue
                self.expression(element, star=True)
            elif 0 < position < len(elements) - 1 or (position == 0 and len(elements) > 1):
                separator = self.comma_before(inner, position)
                self.report(separator, "E407", "Missing Operand",
                            "Empty item between commas: a value is missing.",
                            hint="Remove the extra ',' or put a value between the commas.")

    @staticmethod
    def group_end(tokens: list[Token], start: int) -> int:
        """Index just after the matching closing bracket (or the end, if it never closes)."""
        depth = 0
        for index in range(start, len(tokens)):
            if is_delim(tokens[index], "(", "[", "{"):
                depth += 1
            elif is_delim(tokens[index], ")", "]", "}"):
                depth -= 1
                if depth == 0:
                    return index + 1
        return len(tokens)

    def split_elements(self, tokens: list[Token]) -> list[list[Token]]:
        """Split at top-level commas, keeping a lambda's parameters together (Python)."""
        elements: list[list[Token]] = [[]]
        depth = open_lambdas = 0
        for token in tokens:
            if is_delim(token, "(", "[", "{"):
                depth += 1
            elif is_delim(token, ")", "]", "}"):
                depth -= 1
            elif depth == 0 and token.text == "lambda":
                open_lambdas += 1
            elif depth == 0 and open_lambdas and is_delim(token, ":"):
                open_lambdas -= 1
            elif depth == 0 and not open_lambdas and is_delim(token, ","):
                elements.append([])
                continue
            elements[-1].append(token)
        if len(elements) > 1 and not elements[-1]:
            elements.pop()                              # a trailing comma is allowed
        return elements

    @staticmethod
    def split_top(tokens: list[Token], separator: str) -> list[list[Token]]:
        parts: list[list[Token]] = [[]]
        depth = 0
        for token in tokens:
            if is_delim(token, "(", "[", "{"):
                depth += 1
            elif is_delim(token, ")", "]", "}"):
                depth -= 1
            if depth == 0 and token.text == separator and token.kind is TokenKind.DELIMITER:
                parts.append([])
            else:
                parts[-1].append(token)
        return parts

    @staticmethod
    def comma_before(tokens: list[Token], element: int) -> Token:
        count = 0
        depth = 0
        for token in tokens:
            if is_delim(token, "(", "[", "{"):
                depth += 1
            elif is_delim(token, ")", "]", "}"):
                depth -= 1
            elif depth == 0 and is_delim(token, ","):
                if count == max(element - 1, 0):
                    return token
                count += 1
        return tokens[0]

    # --------------------------------------------------------- special forms

    def is_operand(self, token: Token) -> bool:
        if token.kind in (TokenKind.IDENTIFIER, TokenKind.NUMBER, TokenKind.STRING,
                          TokenKind.CHAR, TokenKind.INVALID):
            return True
        if token.text in VALUE_KEYWORDS:
            return True
        return self.python and token.text == "..."

    def is_cast(self, tokens: list[Token], start: int, end: int) -> bool:
        """'(int) x' or '(String) obj': a type in parentheses followed by a value."""
        inner = tokens[start + 1: end - 1]
        following = tokens[end] if end < len(tokens) else None
        if not inner or following is None or skip_type(inner, 0) != len(inner):
            return False
        first = inner[0]
        looks_like_type = first.text in C_PRIMITIVES or (
            first.kind is TokenKind.IDENTIFIER and first.text[:1].isupper()
        )
        starts_value = following.kind in (
            TokenKind.IDENTIFIER, TokenKind.NUMBER, TokenKind.STRING, TokenKind.CHAR
        ) or following.text in VALUE_KEYWORDS or following.text in ("(", "!", "~", "new")
        return looks_like_type and starts_value

    def skip_lambda(self, tokens: list[Token], index: int) -> int:
        """Skip 'lambda x, y:'; the body that follows is checked as an expression."""
        depth = 0
        for position in range(index + 1, len(tokens)):
            token = tokens[position]
            if is_delim(token, "(", "[", "{"):
                depth += 1
            elif is_delim(token, ")", "]", "}"):
                depth -= 1
            elif depth == 0 and is_delim(token, ":"):
                return position + 1
        return len(tokens)

    def skip_new(self, tokens: list[Token], index: int) -> int:
        """Skip 'new Type(args)', 'new int[n]' or 'new int[] {1, 2}', checking the parts."""
        position = skip_type(tokens, index + 1)
        if position is None:
            return index + 1
        while position < len(tokens) and is_delim(tokens[position], "(", "[", "{"):
            end = self.group_end(tokens, position)
            if tokens[position].text != "{" or tokens[position - 1].text == "]":
                self.group(tokens, position, end, after_value=tokens[position].text != "{")
            position = end
        return position

    def skip_instanceof(self, tokens: list[Token], index: int) -> int:
        """Skip 'instanceof Type' and an optional pattern variable: 'instanceof String s'."""
        position = skip_type(tokens, index + 1) or index + 1
        if position < len(tokens) and tokens[position].kind is TokenKind.IDENTIFIER:
            position += 1
        return position

    def check_target(self, target: list[Token], operator: Token) -> None:
        problem = assignment_problem(target, python=self.python)
        if problem:
            what, culprit = problem
            self.report(culprit, "E404", "Invalid Assignment Target",
                        f"Cannot assign to {what} '{_text(target)}'. Only a variable, "
                        f"attribute or list element can be on the left of '{operator.text}'.",
                        hint="Put a variable name on the left side, e.g. total = 5.")

    # -------------------------------------------------------------- reporting

    def report(self, token: Token, code: str, category: str, message: str, **extra) -> None:
        self.diagnostics.append(
            at(token, Check.OPERATORS, code, category, message, statement=self.statement, **extra)
        )

    def report_consecutive(self, first: Token, second: Token) -> None:
        hint = None
        if first.end_col == second.col and first.line == second.line:
            hint = _PAIR_HINTS.get((first.text, second.text))
        self.report(second, "E401", "Invalid Operator Sequence",
                    f"Consecutive binary operators '{first.text} {second.text}' "
                    "without an operand in between.",
                    hint=hint or "Remove one of the operators, or put a value between them.")

    def report_missing_operand(self, operator: Token, tokens: list[Token]) -> None:
        if self.python and operator.text == "+" and len(tokens) >= 2 and tokens[-2].text == "+":
            self.report(tokens[-2], "E401", "Invalid Operator Sequence",
                        "Python has no '++' operator.", hint="Use 'x += 1' to add one.")
            return
        if self.python and operator.text == "-" and len(tokens) >= 2 and tokens[-2].text == "-":
            self.report(tokens[-2], "E401", "Invalid Operator Sequence",
                        "Python has no '--' operator.", hint="Use 'x -= 1' to subtract one.")
            return
        self.report(operator, "E402", "Missing Operand",
                    f"Missing operand after '{operator.text}'. The expression ends where a "
                    "value is expected.",
                    hint=f"Add a value after '{operator.text}', or remove the operator.")

    def report_missing_operator(self, left: Token, right: Token, tokens: list[Token]) -> None:
        keyword = _keyword_suggestion(left.text, self.profile)
        if self.python and left.text == "print" and left is tokens[0]:
            self.report(left, "E403", "Missing Parentheses",
                        "Missing parentheses in call to 'print'.",
                        hint="In Python 3, print is a function: print(\"Hello\").")
        elif keyword and left is tokens[0]:
            self.report(left, "E403", "Unknown Keyword",
                        f"'{left.text}' is not a keyword, so '{right.text}' cannot follow it.",
                        hint=f"Did you mean '{keyword}'?")
        else:
            self.report(right, "E403", "Missing Operator",
                        f"Missing operator between '{left.text}' and '{right.text}'.",
                        hint="Add an operator (such as + or ==) or a comma between them.")


def assignment_problem(target: list[Token], *, python: bool) -> tuple[str, Token] | None:
    """Explain why ``target`` cannot be assigned to, or return None if it can.

    Names, attributes (obj.x) and list elements (a[0]) can be assigned to, as can
    Python tuples of them (a, *rest).  Literals, calls and calculations cannot.
    Keywords and badly formed names are left to the identifier check.
    """
    from .checks.identifiers import broken_name  # local import: avoids a cycle

    if not target or broken_name(target):
        return None
    parts = _split_commas(target) if python else [target]
    for part in parts:
        if python and part and part[0].text == "*":
            part = part[1:]
        if not part:
            continue
        first = part[0]
        if is_delim(first, "(", "[") and ExpressionChecker.group_end(part, 0) == len(part):
            inner = part[1:-1]
            problem = assignment_problem(inner, python=python) if inner else None
            if problem:
                return problem
            continue
        if len(part) == 1:
            if first.kind in (TokenKind.NUMBER, TokenKind.STRING, TokenKind.CHAR):
                return "the literal", first
            continue
        depth = 0
        for token in part:
            if is_delim(token, "(", "[", "{"):
                depth += 1
            elif is_delim(token, ")", "]", "}"):
                depth -= 1
            elif depth == 0 and token.kind is TokenKind.OPERATOR:
                return "the expression", first
        if part[-1].text == ")":
            return "the function call", first
    return None


def _split_commas(tokens: list[Token]) -> list[list[Token]]:
    return ExpressionChecker.split_top(tokens, ",")


def _keyword_suggestion(word: str, profile: LanguageProfile) -> str | None:
    """A keyword that ``word`` is probably a typo of ('retrun' -> 'return')."""
    if not word.isidentifier() or word in profile.keywords:
        return None
    if word.lower() in profile.keywords:
        return word.lower()
    matches = difflib.get_close_matches(word, sorted(profile.keywords), n=1, cutoff=0.8)
    return matches[0] if matches else None


def _text(tokens: list[Token]) -> str:
    return " ".join(token.text for token in tokens)
