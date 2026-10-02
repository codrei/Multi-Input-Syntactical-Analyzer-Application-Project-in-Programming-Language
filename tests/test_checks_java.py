"""Each of the eight checks on small Java inputs, plus valid programs.

The valid programs are also compiled with the real Java compiler when it is
installed (it is on the GitHub Actions machines), which proves they really are
valid Java.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze, analyze_text
from syntaxlens.source import from_file

CORPUS = sorted((Path(__file__).parent / "data" / "java_valid").glob("*.java"))


def in_method(body):
    """Wrap statements in a class and method, as Java requires."""
    return "public class T {\n    void run() {\n" + body + "\n    }\n}\n"


def findings(code, wrap=True):
    source = in_method(code) if wrap else code
    offset = 2 if wrap else 0
    return [(d.line - offset, d.code) for d in analyze_text(source, "java").diagnostics]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        # 1 delimiters
        ("if (x > 5 {\n    x = 1;\n}", [(1, "E101")]),
        ('System.out.println("a";', [(1, "E101")]),
        ("int[] a = {1, 2, 3", [(1, "E101")]),
        # 2 literals
        ('String s = "open;', [(1, "E201")]),
        ("char c = 'ab';", [(1, "E204")]),
        ("char c = '';", [(1, "E203")]),
        # 3 terminators
        ("int x = 10\nint y = 5;", [(1, "E301")]),
        ("return x", [(1, "E301")]),
        ("do { x--; } while (x > 0)\nint y = 1;", [(1, "E301")]),
        # 4 operators
        ("int x = 5 + * 2;", [(1, "E401")]),
        ("int x = 5 +;", [(1, "E402")]),
        ("5 = x;", [(1, "E404")]),
        ("x + 1;", [(1, "E406")]),
        ("foo(1, , 2);", [(1, "E407")]),
        # 5 control headers
        ("if x > 5 {\n    x = 1;\n}", [(1, "E502")]),
        ("if () {\n}", [(1, "E501")]),
        ("for (int i = 0, i < 5, i++) {\n}", [(1, "E503")]),
        ("if (x > 5):\n    x = 1;", [(1, "E508")]),
        ("elif (a) {\n}", [(1, "E504")]),
        ("switch (x) {\n case 1\n   y = 1;\n   break;\n}", [(2, "E507")]),
        ("if (x = 5) {\n}", [(1, "W505")]),
        ("if (x > 5);\n{ x = 1; }", [(1, "W509")]),
        # 6 identifiers
        ("int 2x = 5;", [(1, "E601")]),
        ("int my-var = 3;", [(1, "E602")]),
        ("int for = 3;", [(1, "E603")]),
        ("int = 5;", [(1, "E604")]),
        # 7 blocks
        ("else {\n}", [(1, "E705")]),
        ("break;", [(1, "E706")]),
        # 8 lexical
        ("double d = 3.14.15;", [(1, "E802")]),
        ("int #x = 1;", [(1, "E801")]),
        ("int x = 1; /* never closed", [(1, "E803")]),
    ],
)
def test_each_mistake_is_found(code, expected):
    assert findings(code) == expected


def test_single_line_without_semicolon():
    assert findings('System.out.println("Hello")', wrap=False) == [(1, "E301")]
    assert findings('System.out.println("Hello");', wrap=False) == []


def test_case_outside_switch():
    assert (1, "E708") in findings("case 1: x = 1;")


@pytest.mark.parametrize(
    "code",
    [
        "List<String> names = new ArrayList<>();",
        "Map<String, List<Integer>> m = new HashMap<>();",
        "double avg = (double) sum / count;",
        "Runnable r = () -> { System.out.println(1); };",
        "names.forEach(n -> System.out.println(n));",
        "int x = y > 0 ? y : -y;",
        "boolean b = obj instanceof String s;",
        "if (a) x = 1; else x = 2;",
        "if (a) { x = 1; } else if (b) { x = 2; } else { x = 3; }",
        "for (String s : names) {\n}",
        "int a[] = {1, 2, 3};",
        "int[] a = {\n    1, 2, 3\n};",
        "Object o = new Object() {\n  public String toString() { return \"x\"; }\n};",
        "int x = 1 /* comment */ + 2; // done",
        "String[] arr = new String[5];",
        "x = y = 0;",
        "a[i++] = 5;",
        "super.run();",
        "i++;",
    ],
)
def test_valid_java_has_no_findings(code):
    assert findings(code) == []


@pytest.mark.parametrize("path", CORPUS, ids=lambda path: path.name)
def test_valid_programs_have_no_findings(path):
    assert analyze(from_file(path)).diagnostics == []


@pytest.mark.skipif(shutil.which("javac") is None, reason="the Java compiler is not installed")
@pytest.mark.parametrize("path", CORPUS, ids=lambda path: path.name)
def test_valid_programs_really_compile(path, tmp_path):
    result = subprocess.run(
        ["javac", "-d", str(tmp_path), str(path)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
