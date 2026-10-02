"""Cross-check: our Python lexer must split valid code exactly like CPython does.

CPython's ``tokenize`` module is the reference.  For every sample program we
compare the text and starting position of every token.  Layout tokens that
CPython emits but we do not (NEWLINE, INDENT, ...) are skipped.  From Python
3.12 on, ``tokenize`` splits f-strings into pieces; those pieces are joined
back into one token, as our lexer reports them.
"""

import io
import tokenize as cpython_tokenize
from pathlib import Path

import pytest

from syntaxlens.lexer import tokenize
from syntaxlens.profiles import PYTHON
from syntaxlens.source import from_text

SAMPLES = sorted((Path(__file__).parent / "data" / "python_valid").glob("*.py"))

_LAYOUT = {
    cpython_tokenize.NEWLINE,
    cpython_tokenize.NL,
    cpython_tokenize.INDENT,
    cpython_tokenize.DEDENT,
    cpython_tokenize.ENDMARKER,
}


def cpython_tokens(code):
    lines = code.splitlines(keepends=True)

    def offset(row, col):
        return sum(len(line) for line in lines[: row - 1]) + col

    result, depth, start = [], 0, None
    for token in cpython_tokenize.generate_tokens(io.StringIO(code).readline):
        name = cpython_tokenize.tok_name[token.type]
        if name.endswith("STRING_START"):  # FSTRING_START (3.12+), TSTRING_START (3.14+)
            if depth == 0:
                start = token.start
            depth += 1
        elif name.endswith("STRING_END"):
            depth -= 1
            if depth == 0:
                result.append((code[offset(*start): offset(*token.end)], start))
        elif depth == 0 and token.type not in _LAYOUT:
            result.append((token.string, token.start))
    return result


def test_samples_exist():
    assert len(SAMPLES) >= 5


@pytest.mark.parametrize("path", SAMPLES, ids=lambda path: path.name)
def test_python_lexer_agrees_with_cpython(path):
    code = path.read_text(encoding="utf-8")
    compile(code, str(path), "exec")  # each sample must be valid Python
    tokens = tokenize(from_text(code), PYTHON).tokens
    ours = [(token.text, (token.line, token.col - 1)) for token in tokens]
    assert ours == cpython_tokens(code)
