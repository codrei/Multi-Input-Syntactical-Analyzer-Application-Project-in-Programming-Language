"""Pointers (C, C++), lambdas and initializers (C++, C#) and generic declarations.

These constructs are valid code that used to be reported as errors.  Each rule
is switched on only for the languages that have it (see profiles/rules.py), and
the last tests show that turning a rule off brings the old behavior back.
"""

from dataclasses import replace

import pytest

from syntaxlens.analyzer import analyze_text
from syntaxlens.profiles import CPP, C
from tests.test_language_rules import run_with


def findings(code, language):
    return [(d.line, d.code) for d in analyze_text(code, language).diagnostics]


def in_main(body):
    return "int main(void) {\n" + body + "\n    return 0;\n}\n"


@pytest.mark.parametrize(
    "body",
    [
        "int temp = *a;",
        "*a = *b;",
        "int *p = &x;",
        "Point *pp = &p;",
        "node->value = value;",
        "p->next->value = 5;",
        "x = *p + 1;",
        "swap(&a, &b);",
        'printf("%d", *ptr);',
        "struct Node *node = (struct Node *) malloc(sizeof(struct Node));",
        "size_t n = (size_t) len;",
        "char *s = (char *) buffer;",
        "for (struct Node *it = list; it != NULL; it = it->next) {\n}",
    ],
)
@pytest.mark.parametrize("language", ["c", "cpp"])
def test_pointer_code_is_valid(body, language):
    assert findings(in_main(body), language) == []


@pytest.mark.parametrize("language", ["c", "cpp"])
def test_a_star_before_a_number_is_still_an_error(language):
    assert findings(in_main("int y = 20 + * 5;"), language) == [(2, "E401")]


@pytest.mark.parametrize(
    "body",
    [
        "ref += *ptr;",
        "auto doubled = [](int v) { return v * 2; };",
        'std::string raw = R"(C:\\path\\with "quotes")";',
        "Point a{1, 2}, b{3, 4};",
        "std::vector<int> v{1, 2, 3};",
        "std::sort(v.begin(), v.end(), [](int a, int b) { return a < b; });",
        "obj->method();",
    ],
)
def test_cpp_lambdas_raw_strings_and_brace_initialization(body):
    assert findings(in_main(body), "cpp") == []


def test_cpp_return_of_a_braced_list():
    code = "struct Point {\n    int x;\n    Point twice() const { return {x * 2}; }\n};\n"
    assert findings(code, "cpp") == []


def test_csharp_property_initializer_and_generic_new():
    code = (
        "public class S\n{\n"
        '    public string Name { get; protected set; } = "shape";\n'
        "    void Run()\n    {\n"
        "        Dictionary<string, int> counts = new Dictionary<string, int>();\n"
        "    }\n}\n"
    )
    assert findings(code, "csharp") == []


def test_java_generic_declaration_with_two_type_arguments():
    code = (
        "class T {\n    void run() {\n"
        "        Map<String, Integer> m = new HashMap<String, Integer>(), other = null;\n"
        "    }\n}\n"
    )
    assert findings(code, "java") == []


@pytest.mark.parametrize("language", ["c", "csharp", "java"])
def test_a_bad_hexadecimal_number_is_a_malformed_number(language):
    code = "class T { void f() { int hex = 0xG1; } }" if language != "c" else in_main("int hex = 0xG1;")
    assert [code_ for _, code_ in findings(code, language)] == ["E802"]


def test_turning_pointers_off_brings_the_errors_back():
    without_pointers = replace(C, rules=replace(C.rules, pointer_operators=False))
    assert run_with(without_pointers, in_main("*a = *b;")) != []
    assert run_with(C, in_main("*a = *b;")) == []


def test_turning_brace_initialization_off_brings_the_errors_back():
    without = replace(CPP, rules=replace(CPP.rules, brace_initialization=False))
    assert run_with(without, in_main("Point a{1, 2};")) != []
    assert run_with(CPP, in_main("Point a{1, 2};")) == []
