"""Command-line interface.

Phase 1 provides the ``tokens`` command, which shows the lexer's output:
every token with its category, then totals per category.  It already accepts
all three input modes:

    python -m syntaxlens tokens --line "y = 20 + * 5"        (mode 1: single line)
    python -m syntaxlens tokens --stdin < snippet.txt        (mode 2: code block)
    python -m syntaxlens tokens samples/spec_example_1.py    (mode 3: file)

The full analysis commands (``line``, ``block``, ``file`` and ``web``) come in
Phase 4.  Exit codes: 0 = success, 2 = the input could not be analyzed.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .detect import detect_language
from .lexer import tokenize
from .profiles import PROFILES
from .report.text import format_token_listing
from .source import InputError, Source, from_file, from_text

EXIT_OK = 0
EXIT_BAD_INPUT = 2


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
