"""Command-line interface.

One command per input mode prints the SYNTACTICAL ANALYSIS REPORT:

    python -m syntaxlens line "x = 10"                      (mode 1: single line)
    python -m syntaxlens block                              (mode 2: code block)
    python -m syntaxlens file samples/spec_example_2.py     (mode 3: file)

``tokens`` shows the lexer's output instead: every token with its category,
then totals per category.  It accepts the same three kinds of input.

Exit codes: 0 = no syntax errors, 1 = syntax errors found, 2 = the input
could not be analyzed (missing, empty or binary file).
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .analyzer import analyze
from .detect import detect_language
from .lexer import tokenize
from .profiles import PROFILES
from .report.text import format_report, format_token_listing
from .source import InputError, Source, from_file, from_text

EXIT_OK = 0
EXIT_ERRORS_FOUND = 1
EXIT_BAD_INPUT = 2

#: A line holding only this ends a code block typed into ``syntaxlens block``.
BLOCK_END_MARKER = "."


def main(argv: list[str] | None = None) -> int:
    """Run the command line and return the exit code."""
    _never_crash_on_output()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_OK
    try:
        return args.handler(args)
    except InputError as error:
        print(f"syntaxlens: {error}", file=sys.stderr)
        return EXIT_BAD_INPUT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="syntaxlens",
        description="SyntaxLens: a multi-input syntactical analyzer.",
    )
    parser.add_argument("--version", action="version", version=f"SyntaxLens {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    language = argparse.ArgumentParser(add_help=False)
    language.add_argument(
        "--lang",
        choices=["auto", *PROFILES],
        default="auto",
        help="language rules to apply (default: auto-detect)",
    )

    line = commands.add_parser(
        "line", parents=[language], help="analyze a single line of code (input mode 1)"
    )
    line.add_argument("code", help='the code, in quotes, e.g. "x = 10"')
    line.set_defaults(handler=_run_analysis, mode="line")

    block = commands.add_parser(
        "block", parents=[language], help="analyze a block of code typed or pasted (input mode 2)"
    )
    block.set_defaults(handler=_run_analysis, mode="block")

    file = commands.add_parser(
        "file", parents=[language], help="analyze a source file (input mode 3)"
    )
    file.add_argument("path", help="file to analyze: .py, .java, .txt, ...")
    file.set_defaults(handler=_run_analysis, mode="file")

    tokens = commands.add_parser(
        "tokens",
        help="list every token with its category, then totals per category",
        description="Show how the lexer splits code into tokens (8 categories, with totals).",
    )
    source = tokens.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?", help="source file to read (input mode 3)")
    source.add_argument("-l", "--line", metavar="CODE", help="one line of code (input mode 1)")
    source.add_argument(
        "--stdin",
        action="store_true",
        help="read a block of code from standard input (input mode 2)",
    )
    tokens.add_argument(
        "--lang",
        choices=["auto", *PROFILES],
        default="auto",
        help="language rules to apply (default: auto-detect)",
    )
    tokens.set_defaults(handler=_run_tokens)
    return parser


def _run_analysis(args: argparse.Namespace) -> int:
    if args.mode == "line":
        source = from_text(args.code, name="<single line>")
    elif args.mode == "block":
        source = from_text(_read_block(), name="<code block>")
    else:
        source = from_file(args.path)
    if source.is_blank:
        raise InputError(f"{source.name} is empty: there is no code to analyze.")
    result = analyze(source, args.lang)
    print(format_report(result))
    return EXIT_OK if result.passed else EXIT_ERRORS_FOUND


def _read_block() -> str:
    """Read lines until a line holding only '.' or the end of input (Ctrl+Z / Ctrl+D)."""
    if sys.stdin.isatty():
        print("Type or paste your code. End with a line containing only '.'")
        print("(or press Ctrl+Z then Enter on Windows, Ctrl+D on macOS/Linux).")
    lines = []
    for line in sys.stdin:
        if line.rstrip("\r\n") == BLOCK_END_MARKER:
            break
        lines.append(line)
    return "".join(lines)


def _run_tokens(args: argparse.Namespace) -> int:
    source = _read_input(args)
    detection = detect_language(source, args.lang)
    result = tokenize(source, detection.profile)
    print(format_token_listing(source, detection, result))
    return EXIT_OK


def _read_input(args: argparse.Namespace) -> Source:
    """Build a Source from whichever input mode the user chose."""
    if args.line is not None:
        source = from_text(args.line, name="<single line>")
    elif args.stdin:
        source = from_text(sys.stdin.read(), name="<code block>")
    else:
        source = from_file(args.file)
    if source.is_blank:
        raise InputError(f"{source.name} is empty: there is no code to analyze.")
    return source


def _never_crash_on_output() -> None:
    """Replace characters the console cannot display instead of crashing.

    A Windows console using an old code page cannot print every Unicode
    character, and printing one would normally raise UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
