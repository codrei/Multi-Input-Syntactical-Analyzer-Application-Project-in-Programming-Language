"""C, C++ and C#: preprocessor lines, ``using``, language-specific E406, and valid programs.

The C and C++ valid programs are also compiled with gcc / g++ when they are installed (they are
on the GitHub Actions machines), which proves they really are valid code.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze, analyze_text
from syntaxlens.diagnostics import Severity
from syntaxlens.source import from_file

DATA = Path(__file__).parent / "data"
C_FILES = sorted((DATA / "c_valid").glob("*.c"))
CPP_FILES = sorted((DATA / "cpp_valid").glob("*.cpp"))
CS_FILES = sorted((DATA / "csharp_valid").glob("*.cs"))


def kinds(code, language):
    return [(s.first_line, s.kind) for s in analyze_text(code, language).statements]


def codes(code, language):
    return [(d.line, d.code) for d in analyze_text(code, language).diagnostics]


def in_function(body, language):
    """Wrap statements in the smallest valid program of the language."""
    if language == "csharp":
        return "class T {\n    void Run() {\n" + body + "\n    }\n}\n"
    return "void run() {\n" + body + "\n}\n"


def body_codes(body, language):
    offset = 2 if language == "csharp" else 1
    return [(line - offset, code) for line, code in codes(in_function(body, language), language)]


# ------------------------------------------------------------ valid programs

@pytest.mark.parametrize("path", C_FILES + CPP_FILES + CS_FILES, ids=lambda path: path.name)
def test_valid_programs_have_no_findings(path):
    result = analyze(from_file(path))
    assert [(d.line, d.code, d.message) for d in result.diagnostics] == []


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc is not installed")
@pytest.mark.parametrize("path", C_FILES, ids=lambda path: path.name)
def test_valid_c_programs_really_compile(path):
    run = subprocess.run(["gcc", "-fsyntax-only", str(path)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is not installed")
@pytest.mark.parametrize("path", CPP_FILES, ids=lambda path: path.name)
def test_valid_cpp_programs_really_compile(path):
    run = subprocess.run(["g++", "-std=c++17", "-fsyntax-only", str(path)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


# ------------------------------------------------- preprocessor lines and using

@pytest.mark.parametrize("language", ["c", "cpp", "csharp"])
def test_preprocessor_lines_are_their_own_statements(language):
    code = '#include <stdio.h>\n#define MAX 10\n#pragma once\n#region Demo\nint x = 1;\n'
    assert kinds(code, language)[:4] == [(1, "preprocessor"), (2, "preprocessor"),
                                         (3, "preprocessor"), (4, "preprocessor")]
    assert codes(code, language) == []


def test_preprocessor_line_continues_after_a_backslash():
    code = "#define LOG(msg) \\\n    printf(msg)\nint x = 1;\n"
    assert kinds(code, "c") == [(1, "preprocessor"), (3, "declaration")]
    assert codes(code, "c") == []


def test_unbalanced_brackets_inside_a_macro_are_not_reported():
    assert codes("#define OPEN {\nint x = 1;\n", "c") == []


def test_java_still_rejects_a_hash_character():
    assert [code for _, code in codes("#include <x>\n", "java")] != []


@pytest.mark.parametrize(
    ("code", "language"),
    [
        ("using System;", "csharp"),
        ("using System.Collections.Generic;", "csharp"),
        ("using static System.Math;", "csharp"),
        ("using Alias = System.Text.StringBuilder;", "csharp"),
        ("global using System;", "csharp"),
        ("using namespace std;", "cpp"),
        ("using std::cout;", "cpp"),
        ("using Names = std::vector<std::string>;", "cpp"),
    ],
)
def test_using_directives_and_aliases(code, language):
    assert kinds(code + "\n", language) == [(1, "using")]
    assert codes(code + "\n", language) == []


def test_using_statement_and_using_declaration_in_csharp_are_not_directives():
    code = ("class T {\n    void Run() {\n        using (var r = Open()) {\n            r.Read();\n"
            "        }\n        using var f = Open();\n    }\n}\n")
    assert [kind for _, kind in kinds(code, "csharp")] == [
        "class", "method", "context", "call", "block_end", "declaration", "block_end", "block_end",
    ]
    assert codes(code, "csharp") == []


def test_a_missing_semicolon_before_using_is_still_found():
    assert codes("using System\nusing System.Linq;\n", "csharp") == [(1, "E301")]


# ------------------------------------------------------- E406 by language

@pytest.mark.parametrize("language", ["java", "csharp"])
@pytest.mark.parametrize("body", ["x + 1;", "x;", "5;", "x == 1;", "x > 0 && y > 0;"])
def test_java_and_csharp_reject_a_discarded_value(body, language):
    assert body_codes(body, language) == [(1, "E406")]


@pytest.mark.parametrize(
    "body",
    [
        "x++;", "--x;", "x = x + 1;", "Foo();", "obj.Run(1, 2);", "new Thing();",
        "await Foo();", "await task;", "obj?.Run();", "obj!.Run();", "Run<int>(5);",
        "list.Cast<string>().ToList();", "_ = Foo();",
    ],
)
def test_csharp_accepts_its_statement_expressions(body):
    assert body_codes(body, "csharp") == []


def test_csharp_property_accessors_are_not_discarded_values():
    code = ("class T {\n    public int X { get; private set; }\n"
            "    public int Y {\n        get { return 1; }\n        set { }\n    }\n}\n")
    assert codes(code, "csharp") == []


@pytest.mark.parametrize("language", ["c", "cpp"])
@pytest.mark.parametrize(
    "body",
    [
        "x + 1;", "x == 1;", "x;", "(void)x;", "x++;", "foo();", "ok && foo();",
        "ok ? foo() : bar();", "FLUSH;", "p->run();", "n * m;",
    ],
)
def test_c_and_cpp_never_report_e406(body, language):
    assert "E406" not in [code for _, code in body_codes(body, language)]


@pytest.mark.parametrize("language", ["c", "cpp"])
def test_a_discarded_value_in_c_and_cpp_is_only_a_warning(language):
    result = analyze_text(in_function("x + 1;", language), language)
    assert [(d.code, d.severity) for d in result.diagnostics] == [("W406", Severity.WARNING)]
    assert result.passed


@pytest.mark.parametrize("language", ["c", "cpp"])
@pytest.mark.parametrize("body", ["x;", "(void)x;", "foo();", "ok && foo();", "ok ? foo() : bar();"])
def test_c_and_cpp_stay_quiet_about_common_valid_idioms(body, language):
    assert body_codes(body, language) == []


def test_real_operator_errors_are_still_found_in_every_language():
    for language in ("c", "cpp", "csharp"):
        assert body_codes("int x = 5 + * 2;", language) == [(1, "E401")]
        assert body_codes("5 = x;", language) == [(1, "E404")]


# ------------------------------------------------------------ stream chains

@pytest.mark.parametrize(
    ("statement", "kind"),
    [
        ("cout << a << endl;", "output"),
        ('std::cout << "a = " << a << std::endl;', "output"),
        ("std::cerr << x;", "output"),
        ("cin >> x >> y;", "call"),
        ("std::cin >> x;", "call"),
        ('out << "total: " << total;', "call"),
    ],
)
def test_cpp_stream_chains_are_call_like_statements(statement, kind):
    assert kinds(in_function(statement, "cpp"), "cpp")[1] == (2, kind)
    assert body_codes(statement, "cpp") == []


def test_a_shift_assignment_is_not_a_stream_chain():
    assert kinds(in_function("x <<= 2;", "cpp"), "cpp")[1] == (2, "assignment")


def test_c_has_no_stream_chains():
    assert kinds(in_function("x << 2;", "c"), "c")[1] == (2, "expression")


# ------------------------------------------------- parameters: void, string[]

@pytest.mark.parametrize("language", ["c", "cpp"])
@pytest.mark.parametrize(
    "header",
    [
        "int main(void) {", "int counter(void) {", "void f(int n, ...) {",
        "int sum(const int *values, size_t count) {", "int main(int argc, char **argv) {",
        "void g(unsigned long long n) {", "void h(struct Node *node) {",
    ],
)
def test_c_parameters_are_accepted(header, language):
    assert codes(header + "\n}\n", language) == []


@pytest.mark.parametrize("language", ["c", "cpp"])
def test_c_prototypes_may_leave_the_parameter_names_out(language):
    assert codes("int add(int, int);\nvoid f(void);\n", language) == []


def test_cpp_direct_initialization_is_a_variable_not_a_function():
    assert codes(in_function('std::string s("text");\nPoint p(1, 2);', "cpp"), "cpp") == []


@pytest.mark.parametrize(
    "header",
    [
        "static void Main(string[] args) {", "static async Task Main(string[] args) {",
        "public int Sum(int[] values, string? label) {", "void Log(params string[] lines) {",
        "void Swap(ref int a, out int b) {", "static void Print(this string text) {",
        "public object Find(decimal price, uint count) {",
    ],
)
def test_csharp_parameters_are_accepted(header):
    assert codes("class T {\n" + header + "\n}\n}\n", "csharp") == []


def test_void_is_still_not_a_parameter_in_java_and_csharp():
    assert codes("class T {\n    void run(void) {\n    }\n}\n", "java") == [(2, "E506")]
    assert codes("class T {\n    void Run(void) {\n    }\n}\n", "csharp") == [(2, "E506")]


def test_a_parameter_without_a_name_is_still_an_error_in_java_and_csharp():
    assert codes("class T {\n    void run(int) {\n    }\n}\n", "java") == [(2, "E506")]
    assert codes("class T {\n    void Run(string) {\n    }\n}\n", "csharp") == [(2, "E506")]


# ------------------------------------------------- the error samples still work

@pytest.mark.parametrize("name", ["errors_demo.c", "errors_demo.cpp", "errors_demo.cs"])
def test_error_samples_still_report_their_mistakes(name):
    result = analyze(from_file(Path(__file__).parent.parent / "samples" / name))
    found = {d.code for d in result.errors}
    assert {"E301", "E401", "E101"} <= found
    assert "E406" not in found
