"""Check 3 in the C family: a missing ';' is found on its own line, and valid layouts stay quiet.

A missing ';' is spotted when a statement is complete at the end of a line and the next line
starts a new one (structure.py).  These tests cover the line starts that are easy to miss
(std::string, p->x, cout <<, --x), statements that look unfinished (break, prototypes,
'= default'), the ';' after a struct body in C and C++, and the planted-mistake measurement.
"""

import importlib.util
from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze_text
from syntaxlens.diagnostics import Check


def codes(code, language):
    return [(d.line, d.code) for d in analyze_text(code, language).diagnostics]


# ------------------------------------------------------------ a missing ';' is found

@pytest.mark.parametrize(
    ("language", "code", "line"),
    [
        ("cpp", "int main() {\n    int a = 5\n    std::string name = \"Ada\";\n}\n", 2),
        ("cpp", "int main() {\n    int a = 5\n    cout << a;\n}\n", 2),
        ("cpp", "int main() {\n    int a = 5\n    std::cout << a;\n}\n", 2),
        ("cpp", "int main() {\n    bool ok = true\n    auto total = 0;\n}\n", 2),
        ("cpp", "int main() {\n    int *p = new int(1)\n    delete p;\n}\n", 2),
        ("c", "int main(void) {\n    Point *pp = &p\n    pp->x = 2;\n}\n", 2),
        ("c", "int main(void) {\n    char *s = name\n    unsigned int n = 0;\n}\n", 2),
        ("c", "int main(void) {\n    enum Color c = RED\n    int n = 0;\n}\n", 2),
        ("c", "int add(int a, int b)\nint sub(int a, int b);\n", 1),
        ("csharp", "class T {\n    void Run() {\n        total++\n        --total;\n    }\n}\n", 3),
        ("java", "class T {\n    void run() {\n        while (true) {\n            break\n        }\n"
                 "    }\n}\n", 4),
        ("java", "class T {\n    void run(int x) {\n        switch (x) {\n            case 1:\n"
                 "                x++;\n                break\n            default:\n"
                 "                x--;\n        }\n    }\n}\n", 6),
        ("java", "interface Shape {\n    double area()\n}\n", 2),
        ("java", "class T {\n    void run(int n) {\n        do {\n            n++;\n        } while (n < 3)\n"
                 "        outer:\n        for (;;) { break outer; }\n    }\n}\n", 5),
    ],
)
def test_a_missing_semicolon_is_reported_on_its_line(language, code, line):
    assert (line, "E301") in codes(code, language)


def test_c_struct_member_without_semicolon():
    code = "struct Node {\n    int value;\n    struct Node *next\n};\n"
    assert codes(code, "c") == [(3, "E301")]


@pytest.mark.parametrize("language", ["c", "cpp"])
def test_a_struct_body_needs_a_semicolon_in_c_and_cpp(language):
    code = "struct Point {\n    int x;\n}\nint main(void) {\n    return 0;\n}\n"
    result = analyze_text(code, language)
    assert [(d.line, d.code) for d in result.diagnostics] == [(3, "E301")]
    assert "'struct' definition" in result.diagnostics[0].message


@pytest.mark.parametrize("language", ["java", "csharp"])
def test_a_class_body_needs_no_semicolon_in_java_and_csharp(language):
    assert codes("class Point {\n    int x;\n}\nclass Line {\n    int y;\n}\n", language) == []


# ------------------------------------------------------------ valid layouts stay quiet

@pytest.mark.parametrize(
    ("language", "code"),
    [
        ("java", "enum Level {\n    LOW,\n    MEDIUM,\n    HIGH\n}\n"),
        ("csharp", "enum Level\n{\n    Low,\n    High\n}\n"),
        ("c", "typedef enum {\n    RED,\n    GREEN\n} Color;\n"),
        ("c", "struct Point {\n    int x, y;\n} origin = {0, 0}, *current = 0;\n"),
        ("c", "struct Node {\n    int v;\n};\nstruct Node *make(int v)\n{\n    return 0;\n}\nint x;\n"),
        ("cpp", "class Shape {\npublic:\n    Shape() = default;\n    Shape(const Shape &) = delete;\n"
                "    virtual ~Shape() = default;\n};\n"),
        ("cpp", "int main() {\n    std::cout << 1\n              << 2\n              << std::endl;\n}\n"),
        ("cpp", "class Circle {\n    explicit Circle(double r)\n        : radius_(r)\n    {\n    }\n"
                "    double area() const\n    {\n        return radius_;\n    }\n    double radius_;\n};\n"),
        ("java", "class T {\n    String read(String s)\n        throws java.io.IOException\n    {\n"
                 "        try (java.io.StringReader r = new java.io.StringReader(s)) {\n"
                 "            return s;\n        }\n    }\n}\n"),
        ("csharp", "[Serializable]\npublic class Repository<T>\n    where T : class, new()\n{\n"
                   "    [Obsolete(\"old\")]\n    public void Add(T item)\n    {\n        int? n = null;\n"
                   "        n ??= 4;\n    }\n}\n"),
    ],
)
def test_valid_layouts_have_no_findings(language, code):
    assert codes(code, language) == []


# ------------------------------------------------------------ the measured catch rate

def test_planted_mistakes_are_caught():
    """tools/measure_accuracy.py plants ~1,200 known mistakes; nearly all must be caught."""
    path = Path(__file__).resolve().parents[1] / "tools" / "measure_accuracy.py"
    spec = importlib.util.spec_from_file_location("measure_accuracy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    totals, _ = module.measure()
    tried = sum(counts[0] for counts in totals.values())
    caught = sum(counts[1] for counts in totals.values())
    assert caught / tried >= 0.97
    for check, (tried, caught, _) in totals.items():
        assert caught / tried >= 0.90, check
    assert set(totals) == set(Check)
