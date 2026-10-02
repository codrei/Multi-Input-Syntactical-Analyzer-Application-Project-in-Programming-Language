import keyword

import pytest

from syntaxlens.lexer import tokenize
from syntaxlens.profiles import PYTHON
from syntaxlens.source import from_text
from syntaxlens.tokens import Issue, TokenCategory, TokenKind, group_by_category


def lex(code):
    return tokenize(from_text(code), PYTHON)


def texts(code):
    return [token.text for token in lex(code).tokens]


SPEC_EXAMPLE_1 = 'x = 10\nif (x > 5):\n    print("Value is valid")\n'


def test_spec_example_1_has_exactly_14_tokens():
    assert texts(SPEC_EXAMPLE_1) == [
        "x", "=", "10",
        "if", "(", "x", ">", "5", ")", ":",
        "print", "(", '"Value is valid"', ")",
    ]


def test_spec_example_1_category_totals():
    groups = group_by_category(lex(SPEC_EXAMPLE_1).tokens)
    counts = {category: len(tokens) for category, tokens in groups.items()}
    assert counts == {
        TokenCategory.KEYWORD: 1,
        TokenCategory.IDENTIFIER: 3,
        TokenCategory.OPERATOR: 2,
        TokenCategory.NUMBER: 2,
        TokenCategory.STRING: 1,
        TokenCategory.DELIMITER: 5,
        TokenCategory.COMMENT: 0,
        TokenCategory.INVALID: 0,
    }


def test_keywords_match_pythons_own_list():
    assert PYTHON.keywords == frozenset(keyword.kwlist)


def test_positions_are_one_based():
    token = lex("x = 1\n    total = 2").tokens[3]
    assert (token.text, token.line, token.col, token.end_col) == ("total", 2, 5, 10)


def test_longest_operator_wins():
    assert texts("a **= b // c -> d := e != f <<= g") == [
        "a", "**=", "b", "//", "c", "->", "d", ":=", "e", "!=", "f", "<<=", "g",
    ]


@pytest.mark.parametrize(
    "code",
    ['"a"', "'b'", r'r"\d+"', 'f"{x}"', 'b"bytes"', "rb'x'", 'u"text"',
     '"""multi\nline"""', "'''x'''", r'"say \"hi\""', '"back\\\nslash"'],
)
def test_valid_strings_are_single_tokens(code):
    tokens = lex(code).tokens
    assert len(tokens) == 1
    assert tokens[0].kind is TokenKind.STRING
    assert tokens[0].issue is None


def test_code_inside_a_string_is_not_tokenized():
    assert texts('msg = "if (x > 0) { y = 5 + * 2"') == ["msg", "=", '"if (x > 0) { y = 5 + * 2"']


def test_unclosed_string_stops_at_end_of_line():
    tokens = lex('print("Value is valid)\ny = 2').tokens
    assert tokens[2].text == '"Value is valid)'
    assert tokens[2].issue is Issue.UNTERMINATED_STRING
    assert [t.text for t in tokens[3:]] == ["y", "=", "2"]  # the next line is read normally


def test_unclosed_triple_quote_runs_to_the_end():
    tokens = lex('x = """never closed\ny = 2\n').tokens
    assert len(tokens) == 3
    assert tokens[2].issue is Issue.UNTERMINATED_STRING
    assert (tokens[2].line, tokens[2].end_line) == (1, 2)


def test_comments_are_tokens():
    tokens = lex("x = 1  # set x").tokens
    assert tokens[-1].text == "# set x"
    assert tokens[-1].kind is TokenKind.COMMENT


@pytest.mark.parametrize(
    "number",
    ["0", "00", "42", "1_000_000", "3.14", ".5", "5.", "1e10", "2.5E-3", "0xFF", "0o17",
     "0b1010", "3j", "1.5j", "1_000.000_1"],
)
def test_valid_numbers(number):
    tokens = lex(number).tokens
    assert [(t.text, t.kind, t.issue) for t in tokens] == [(number, TokenKind.NUMBER, None)]


@pytest.mark.parametrize("number", ["3.14.15", "0b102", "09", "1__0", "0xFG", "1_"])
def test_malformed_numbers_are_one_invalid_token(number):
    tokens = lex(number).tokens
    assert [(t.text, t.kind, t.issue) for t in tokens] == [
        (number, TokenKind.INVALID, Issue.MALFORMED_NUMBER)
    ]


@pytest.mark.parametrize("name", ["2total", "1st", "9lives"])
def test_names_starting_with_a_digit(name):
    token = lex(f"{name} = 5").tokens[0]
    assert (token.text, token.issue) == (name, Issue.NAME_STARTS_WITH_DIGIT)


@pytest.mark.parametrize("char", ["$", "?", "`", "!"])
def test_illegal_characters_become_invalid_tokens(char):
    tokens = lex(f"a {char} b").tokens
    assert [t.text for t in tokens] == ["a", char, "b"]
    assert tokens[1].issue is Issue.ILLEGAL_CHARACTER


def test_not_equal_is_still_an_operator():
    assert lex("a != b").tokens[1].kind is TokenKind.OPERATOR


def test_curly_quotes_are_one_invalid_token():
    tokens = lex("print(“Hello”)").tokens
    assert [t.text for t in tokens] == ["print", "(", "“Hello”", ")"]
    assert tokens[2].issue is Issue.CURLY_QUOTES


def test_curly_quote_closed_by_straight_quote_keeps_the_bracket():
    tokens = lex('print(“Hello")').tokens
    assert [t.text for t in tokens] == ["print", "(", '“Hello"', ")"]


def test_look_alike_spaces_are_recorded_not_tokenized():
    result = lex("x\u00a0= 1")
    assert [t.text for t in result.tokens] == ["x", "=", "1"]
    assert result.odd_spaces == [(1, 2, "\u00a0")]


def test_backslash_continuation_is_recorded():
    result = lex("total = 1 + \\\n    2")
    assert [t.text for t in result.tokens] == ["total", "=", "1", "+", "2"]
    assert result.continued_lines == {1}


def test_unicode_names_are_identifiers():
    assert lex("café = 1").tokens[0].kind is TokenKind.IDENTIFIER


def test_soft_keywords_are_identifiers_to_the_lexer():
    # "match" is only a keyword at the start of a match statement; the lexer cannot know.
    assert lex("match = 5").tokens[0].kind is TokenKind.IDENTIFIER
