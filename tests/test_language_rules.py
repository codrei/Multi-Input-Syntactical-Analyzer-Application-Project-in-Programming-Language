"""Per-language rules: each language declares its grammar surface as data.

The shared code (structure.py, expressions.py, checks/) must never ask "is this C#?".  These
tests pin down the rules of every language, prove that changing a rule changes the behavior, and
guard against language names creeping back into the shared code.
"""

import re
from dataclasses import replace
from pathlib import Path

import pytest

from syntaxlens.analyzer import analyze_text, filter_cascades
from syntaxlens.checks import Context, operators, run_all
from syntaxlens.lexer import tokenize
from syntaxlens.profiles import CPP, CSHARP, JAVA, PROFILES, PYTHON, C
from syntaxlens.profiles.rules import (
    DISCARDED_VALUE_ERROR,
    DISCARDED_VALUE_WARNING,
    LanguageRules,
)
from syntaxlens.source import from_text
from syntaxlens.structure import build_statements

PACKAGE = Path(__file__).parent.parent / "syntaxlens"


def run_with(profile, code):
    """Run the whole pipeline with a profile that was changed by the test."""
    source = from_text(code)
    lex = tokenize(source, profile)
    context = Context(source, lex, build_statements(source, lex))
    return [(d.line, d.code) for d in filter_cascades(run_all(context))]


def codes(code, language):
    return [(d.line, d.code) for d in analyze_text(code, language).diagnostics]


# ------------------------------------------------------------ the rules themselves

def test_every_language_has_rules():
    assert set(PROFILES) == {"python", "java", "c", "cpp", "csharp"}
    assert all(isinstance(profile.rules, LanguageRules) for profile in PROFILES.values())


def test_python_has_no_c_family_rules():
    assert PYTHON.rules == LanguageRules()


@pytest.mark.parametrize(
    ("profile", "field", "expected"),
    [
        (JAVA, "discarded_value", DISCARDED_VALUE_ERROR),
        (CSHARP, "discarded_value", DISCARDED_VALUE_ERROR),
        (C, "discarded_value", DISCARDED_VALUE_WARNING),
        (CPP, "discarded_value", DISCARDED_VALUE_WARNING),
        (JAVA, "preprocessor_lines", False),
        (C, "preprocessor_lines", True),
        (CPP, "preprocessor_lines", True),
        (CSHARP, "preprocessor_lines", True),
        (CPP, "stream_chains", True),
        (C, "stream_chains", False),
        (CPP, "access_labels", True),
        (CSHARP, "access_labels", False),
        (CSHARP, "await_prefix", True),
        (JAVA, "await_prefix", False),
        (C, "void_parameter", True),
        (CPP, "void_parameter", True),
        (JAVA, "void_parameter", False),
        (CSHARP, "void_parameter", False),
        (C, "parameter_names_optional", True),
        (JAVA, "parameter_names_optional", False),
        (JAVA, "self_reference_statements", True),
        (CSHARP, "self_reference_statements", False),
        (JAVA, "arrow_statements", "->"),
        (CSHARP, "arrow_statements", None),
        (JAVA, "parameter_modifiers", frozenset({"final"})),
        (CSHARP, "parameter_modifiers", frozenset({"ref", "out", "in", "params", "this"})),
        (CSHARP, "contextual_modifiers", frozenset({"async", "partial", "required", "global"})),
        (CSHARP, "accessor_names", frozenset({"get", "set", "init", "add", "remove"})),
    ],
)
def test_rule_values(profile, field, expected):
    assert getattr(profile.rules, field) == expected


def test_an_unknown_discarded_value_policy_is_rejected():
    with pytest.raises(ValueError, match="discarded_value"):
        LanguageRules(discarded_value="ignore")


def test_every_policy_has_a_handler():
    assert set(operators._DISCARDED_VALUE) == {DISCARDED_VALUE_ERROR, DISCARDED_VALUE_WARNING}


# ----------------------------------------- changing a rule changes the behavior

def test_the_discarded_value_policy_decides_between_error_and_warning():
    code = "void run() {\n    x + 1;\n}\n"
    assert run_with(CPP, code) == [(2, "W406")]
    strict = replace(CPP, rules=replace(CPP.rules, discarded_value=DISCARDED_VALUE_ERROR))
    assert run_with(strict, code) == [(2, "E406")]
    relaxed = replace(JAVA, rules=replace(JAVA.rules, discarded_value=DISCARDED_VALUE_WARNING))
    assert run_with(relaxed, "class T {\n    void run() {\n        x + 1;\n    }\n}\n") == [(3, "W406")]


def test_the_void_parameter_rule_decides_whether_f_void_is_valid():
    code = "int main(void) {\n}\n"
    assert run_with(C, code) == []
    strict = replace(C, rules=replace(C.rules, void_parameter=False, parameter_names_optional=False))
    assert run_with(strict, code) == [(1, "E506")]
    lenient = replace(JAVA, rules=replace(JAVA.rules, void_parameter=True))
    assert run_with(lenient, "class T {\n    void run(void) {\n    }\n}\n") == []


def test_the_parameter_modifier_rule_decides_what_may_precede_a_type():
    code = "class T {\n    void Run(out int b) {\n    }\n}\n"
    assert run_with(CSHARP, code) == []
    without = replace(CSHARP, rules=replace(CSHARP.rules, parameter_modifiers=frozenset()))
    assert run_with(without, code) == [(2, "E506")]     # 'out' is then taken for the type


def kinds_with(profile, code):
    source = from_text(code)
    return [s.kind for s in build_statements(source, tokenize(source, profile))]


def test_the_preprocessor_rule_decides_whether_hash_lines_are_statements():
    code = "#include <stdio.h>\nint x = 1;\n"
    assert kinds_with(C, code) == ["preprocessor", "declaration"]
    without = replace(C, rules=replace(C.rules, preprocessor_lines=False))
    assert "preprocessor" not in kinds_with(without, code)


def test_the_stream_chain_rule_decides_whether_cout_is_call_like():
    code = "void run() {\n    cout << a << endl;\n}\n"
    off = replace(CPP, rules=replace(CPP.rules, stream_chains=False))
    assert kinds_with(off, code)[1] == "expression"
    assert kinds_with(CPP, code)[1] == "output"
    assert run_with(CPP, code) == []
    assert run_with(off, code) == [(2, "W406")]


def test_the_await_rule_decides_whether_await_is_a_prefix():
    code = "class T {\n    void Run() {\n        var x = await Load();\n    }\n}\n"
    assert run_with(CSHARP, code) == []
    without = replace(CSHARP, rules=replace(CSHARP.rules, await_prefix=False))
    assert run_with(without, code) == [(3, "E403")]


# ------------------------------------------- the same code, in every language

@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("x + 1;", {"java": "E406", "csharp": "E406", "c": "W406", "cpp": "W406"}),
        ("x;", {"java": "E406", "csharp": "E406", "c": None, "cpp": None}),
        ("x++;", {"java": None, "csharp": None, "c": None, "cpp": None}),
        ("run();", {"java": None, "csharp": None, "c": None, "cpp": None}),
        ("this.run();", {"java": None, "csharp": None, "c": None, "cpp": None}),
        ("int x = 5 + * 2;", {"java": "E401", "csharp": "E401", "c": "E401", "cpp": "E401"}),
    ],
)
def test_one_statement_in_every_language(body, expected):
    for language, code in expected.items():
        wrapper = "class T {\n    void run() {\n%s\n    }\n}\n" if language in ("java", "csharp") \
            else "void run() {\n%s\n}\n"
        found = [c for _, c in codes(wrapper % body, language)]
        assert found == ([code] if code else []), language


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("int f(void) {", {"c": [], "cpp": [], "java": ["E506"], "csharp": ["E506"]}),
        ("int f(int n, ...) {", {"c": [], "cpp": [], "java": ["E506"], "csharp": ["E506"]}),
        ("int f(int) {", {"c": [], "cpp": [], "java": ["E506"], "csharp": ["E506"]}),
        ("int f(int n) {", {"c": [], "cpp": [], "java": [], "csharp": []}),
        ("int f(string[] a) {", {"java": [], "csharp": []}),
    ],
)
def test_one_parameter_list_in_every_language(header, expected):
    for language, errors in expected.items():
        found = [c for _, c in codes(f"class T {{\n    {header}\n    }}\n}}\n", language)]
        assert found == errors, language


# ------------------------------------------- no language names in the shared code

SHARED = [PACKAGE / "structure.py", PACKAGE / "expressions.py", *sorted((PACKAGE / "checks").glob("*.py"))]
LANGUAGE_TEST = re.compile(r"""(\.key\s*(==|!=|in|not in)|\blang\s*(==|!=|in)|\bkey\s*(==|!=)\s*["'])""")


@pytest.mark.parametrize("path", SHARED, ids=lambda path: path.name)
def test_shared_code_does_not_branch_on_language_names(path):
    offenders = [(number, line.strip()) for number, line in enumerate(path.read_text().splitlines(), 1)
                 if LANGUAGE_TEST.search(line) and not line.lstrip().startswith("#")]
    assert offenders == []
