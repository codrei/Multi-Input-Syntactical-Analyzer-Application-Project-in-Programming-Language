"""Each of the eight checks on small Python inputs: one known mistake each."""

from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze, analyze_text
from syntaxlens.source import from_file

CORPUS = sorted((Path(__file__).parent / "data" / "python_valid").glob("*.py"))


def findings(code):
    return [(d.line, d.code) for d in analyze_text(code, "python").diagnostics]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        # 1 delimiters
        ("x = (1 + 2", [(1, "E101")]),
        ("x = [1, 2)", [(1, "E103")]),
        ("x = 1)", [(1, "E102")]),
        ("total = (1 +\n         2", [(1, "E101")]),
        # 2 string literals
        ('print("hi)', [(1, "E201")]),
        ("s = '''never closed\nmore", [(1, "E201")]),
        # 3 terminators
        ("if x > 5\n    print(x)", [(1, "E302")]),
        ("if x > 5 {\n    print(x)", [(1, "E302")]),
        ("def f()\n    pass", [(1, "E302")]),
        # 4 operators
        ("y = 20 + * 5", [(1, "E401")]),
        ("x = 5 +", [(1, "E402")]),
        ("x = 5 6", [(1, "E403")]),
        ("5 = x", [(1, "E404")]),
        ("x =", [(1, "E402")]),
        ("f(a,,b)", [(1, "E407")]),
        ("obj. = 5", [(1, "E408")]),
        ('print "hello"', [(1, "E403")]),
        ("retrun x", [(1, "E403")]),
        ("x++", [(1, "E401")]),
        ("a && b", [(1, "E401")]),
        # 5 control headers
        ("if :\n    pass", [(1, "E501")]),
        ("if x = 5:\n    pass", [(1, "E505")]),
        ("for i range(10):\n    pass", [(1, "E503")]),
        ("if x:\n    pass\nelse x > 3:\n    pass", [(3, "E504")]),
        ("if x:\n    pass\nelse if y:\n    pass", [(3, "E504")]),
        ("def :\n    pass", [(1, "E506")]),
        ("def f(a b):\n    pass", [(1, "E509")]),
        ("def f(a=1, b):\n    pass", [(1, "E510")]),
        # 6 identifiers
        ("2total = 5", [(1, "E601")]),
        ("my-var = 3", [(1, "E602")]),
        ("my var = 3", [(1, "E602")]),
        ("class = 5", [(1, "E603")]),
        ("def class():\n    pass", [(1, "E603")]),
        # 7 indentation and blocks
        ("x = 1\n    y = 2", [(2, "E701")]),
        ("while True:\nprint(1)", [(2, "E702")]),
        ("if x:\n        a = 1\n    b = 2", [(3, "E703")]),
        ("if x == 1:\n\tpass\n        pass", [(3, "E704")]),
        ("else:\n    pass", [(1, "E705")]),
        ("break", [(1, "E706")]),
        ("return 5", [(1, "E707")]),
        ("for x in y:\n    def f():\n        break", [(3, "E706")]),
        # 8 lexical
        ("total$ = 5", [(1, "E801")]),
        ("price = 3.14.15", [(1, "E802")]),
        ("y = 0b102", [(1, "E802")]),
        ("z = 09", [(1, "E802")]),
        ("print(\u201cHello\u201d)", [(1, "E804")]),
        ("x\u00a0= 1", [(1, "E805")]),
    ],
)
def test_each_mistake_is_found(code, expected):
    assert findings(code) == expected


@pytest.mark.parametrize(
    "code",
    [
        "x = 10",
        "a, *rest = items",
        "x: int = 5",
        "value = lambda a, b: a + b",
        "print(*args, sep=', ', **kwargs)",
        "matrix[1:3, ::2] = 0",
        "result = [x for x, y in pairs if x not in seen]",
        "ok = a is not None and not b",
        "joined = ('a'\n          'b')",
        "data = {\n    'k': [1, 2],\n}",
        "if (n := len(items)) > 3:\n    pass",
        "x = -5 + +3 - ~2",
        "f(a)(b)[c].d",
        "class A(B, metaclass=M):\n    pass",
        "for i in range(3): print(i)",
        "async def f():\n    await g()",
        "x = yield value",
        "match = 5",
    ],
)
def test_valid_python_has_no_findings(code):
    if "yield" in code:
        code = "def gen():\n    " + code
    assert findings(code) == []


@pytest.mark.parametrize("path", CORPUS, ids=lambda path: path.name)
def test_valid_programs_have_no_findings(path):
    result = analyze(from_file(path))
    assert result.diagnostics == []


def test_errors_on_several_lines_are_all_found():
    """After an error, analysis continues: every independent mistake is reported."""
    code = "x = (1 + 2\ny = 3 +\nprint('ok')\nz = 2abc\n"
    assert findings(code) == [(1, "E101"), (2, "E402"), (4, "E601")]


def test_c_style_condition_habits_are_explained():
    result = analyze_text("if a && b:\n    pass", "python")
    assert result.errors[0].hint == "Python writes logical AND as 'and', not '&&'."
