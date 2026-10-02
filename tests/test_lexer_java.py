import pytest

from syntaxlens.lexer import tokenize
from syntaxlens.profiles import JAVA
from syntaxlens.source import from_text
from syntaxlens.tokens import Issue, TokenCategory, TokenKind, group_by_category


def lex(code):
    return tokenize(from_text(code), JAVA)


def texts(code):
    return [token.text for token in lex(code).tokens]


def test_spec_single_line_example():
    tokens = lex('System.out.println("Hello");').tokens
    assert [t.text for t in tokens] == [
        "System", ".", "out", ".", "println", "(", '"Hello"', ")", ";",
    ]
    counts = {c: len(ts) for c, ts in group_by_category(tokens).items()}
    assert counts[TokenCategory.IDENTIFIER] == 3
    assert counts[TokenCategory.DELIMITER] == 5
    assert counts[TokenCategory.STRING] == 1


def test_keywords_and_type_names():
    tokens = lex("public static void main(String[] args)").tokens
    kinds = {t.text: t.kind for t in tokens}
    assert kinds["public"] is kinds["static"] is kinds["void"] is TokenKind.KEYWORD
    assert kinds["String"] is TokenKind.IDENTIFIER  # a class name, not a keyword


@pytest.mark.parametrize("code", ["'A'", r"'\n'", r"'\''", r"'\u0041'"])
def test_char_literals(code):
    tokens = lex(code).tokens
    assert [(t.kind, t.issue) for t in tokens] == [(TokenKind.CHAR, None)]


def test_unclosed_char_literal():
    token = lex("char c = 'A;\nint x;").tokens[3]
    assert token.kind is TokenKind.CHAR
    assert (token.issue, token.text) == (Issue.UNTERMINATED_STRING, "'A;")


def test_longest_operator_wins():
    assert texts("a >>>= b >>> c -> d :: e ++ --") == [
        "a", ">>>=", "b", ">>>", "c", "->", "d", "::", "e", "++", "--",
    ]


def test_annotations_and_varargs():
    assert texts("@Override void f(String... args)") == [
        "@", "Override", "void", "f", "(", "String", "...", "args", ")",
    ]


def test_block_comment_spanning_lines():
    tokens = lex("/* a\n b */ int x;").tokens
    assert tokens[0].kind is TokenKind.COMMENT
    assert (tokens[0].line, tokens[0].end_line) == (1, 2)
    assert [t.text for t in tokens[1:]] == ["int", "x", ";"]


def test_unclosed_block_comment():
    token = lex("int x; /* oops\nint y;").tokens[-1]
    assert (token.kind, token.issue) == (TokenKind.COMMENT, Issue.UNTERMINATED_COMMENT)


def test_comment_markers_inside_strings_are_text():
    assert texts('s = "// not a comment";') == ["s", "=", '"// not a comment"', ";"]


def test_text_block():
    tokens = lex('String s = """\n    hi\n    """;').tokens
    assert tokens[3].kind is TokenKind.STRING
    assert tokens[3].issue is None
    assert tokens[4].text == ";"


def test_hash_and_backslash_are_illegal_in_java():
    tokens = lex("int #x = 1; \\").tokens
    assert tokens[1].issue is Issue.ILLEGAL_CHARACTER
    assert tokens[-1].issue is Issue.ILLEGAL_CHARACTER


def test_dollar_is_allowed_in_java_names():
    assert lex("int $total = 1;").tokens[1].kind is TokenKind.IDENTIFIER


@pytest.mark.parametrize(
    "number",
    ["0", "42", "10L", "3.14", "3.14f", "2.5d", ".5", "5.", "1e-3", "5f", "0x1F", "0b1010",
     "1_000_000", "017"],
)
def test_valid_numbers(number):
    tokens = lex(number).tokens
    assert [(t.text, t.kind, t.issue) for t in tokens] == [(number, TokenKind.NUMBER, None)]


@pytest.mark.parametrize("number", ["09", "0b12", "1.2.3", "10Lx"])
def test_malformed_numbers(number):
    tokens = lex(number).tokens
    assert [(t.text, t.issue) for t in tokens] == [(number, Issue.MALFORMED_NUMBER)]


def test_name_starting_with_digit():
    token = lex("int 1st = 5;").tokens[1]
    assert (token.text, token.issue) == ("1st", Issue.NAME_STARTS_WITH_DIGIT)
