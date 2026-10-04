"""Command-line interface.

One command per input mode prints the SYNTACTICAL ANALYSIS REPORT:

    python -m syntaxlens line "x = 10"                      (mode 1: single line)
    python -m syntaxlens block                              (mode 2: code block)
    python -m syntaxlens file samples/spec_example_2.py     (mode 3: one or more files)

Running ``python -m syntaxlens`` with no command opens an interactive menu
(see menu.py).  ``tokens`` shows the lexer's output instead of the report.

Options shared by the analysis commands:

    --lang auto|python|java       language rules (default: auto-detect)
    --style detailed|classic      detailed adds codes, column pointers, fixes and
                                  totals per category; classic is the exact layout
                                  of the specification's examples
    --format text|json            report as text (default) or as JSON data
    --output FILE                 save the report to a file instead of printing it
    --no-color                    plain text even in a terminal

Exit codes: 0 = no syntax errors, 1 = syntax errors found, 2 = the input
could not be analyzed (missing, empty or binary file).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyzer import AnalysisResult, analyze
from .console import colorize, enable_colors
from .detect import detect_language
from .lexer import tokenize
from .profiles import PROFILES
from .report.json_report import to_dict, to_json
from .report.text import STYLES, format_report, format_token_listing
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
        if sys.stdin.isatty() and sys.stdout.isatty():
            from .menu import run_menu

            return run_menu()
        parser.print_help()
        return EXIT_OK
    try:
        return args.handler(args)
    except InputError as error:
        print(f"syntaxlens: {error}", file=sys.stderr)
        return EXIT_BAD_INPUT


def render(result: AnalysisResult, style: str = "detailed", fmt: str = "text") -> str:
    """The report for ``result`` as text or JSON."""
    return to_json(result) if fmt == "json" else format_report(result, style)


def read_block(prompt: bool) -> str:
    """Read lines until a line holding only '.' or the end of input (Ctrl+Z / Ctrl+D)."""
    if prompt:
        print("Type or paste your code. End with a line containing only '.'")
        print("(or press Ctrl+Z then Enter on Windows, Ctrl+D on macOS/Linux).")
    lines = []
    for line in sys.stdin:
        if line.rstrip("\r\n") == BLOCK_END_MARKER:
            break
        lines.append(line)
    return "".join(lines)


def require_code(source: Source) -> Source:
    if source.is_blank:
        raise InputError(f"{source.name} is empty: there is no code to analyze.")
    return source


# ------------------------------------------------------------------ parser

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="syntaxlens",
        description="SyntaxLens: a multi-input syntactical analyzer. "
                    "Run it with no command for an interactive menu.",
    )
    parser.add_argument("--version", action="version", version=f"SyntaxLens {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    language = argparse.ArgumentParser(add_help=False)
    language.add_argument("--lang", choices=["auto", *PROFILES], default="auto",
                          help="language rules to apply (default: auto-detect)")
    common = argparse.ArgumentParser(add_help=False, parents=[language])
    common.add_argument("--style", choices=STYLES, default="detailed",
                        help="detailed (default) or classic (the specification's exact layout)")
    common.add_argument("--format", choices=["text", "json"], default="text", dest="fmt",
                        help="report as text (default) or JSON")
    common.add_argument("--output", metavar="FILE", help="save the report to FILE instead of printing it")
    common.add_argument("--no-color", action="store_true", help="never use colors")

    line = commands.add_parser("line", parents=[common],
                               help="analyze a single line of code (input mode 1)")
    line.add_argument("code", help='the code, in quotes, e.g. "x = 10"')
    line.set_defaults(handler=_run_line)

    block = commands.add_parser("block", parents=[common],
                                help="analyze a block of code typed or pasted (input mode 2)")
    block.set_defaults(handler=_run_block)

    file = commands.add_parser("file", parents=[common],
                               help="analyze one or more source files (input mode 3)")
    file.add_argument("paths", nargs="+", metavar="PATH", help="files to analyze: .py, .java, .txt, ...")
    file.set_defaults(handler=_run_files)

    menu = commands.add_parser("menu", help="open the interactive menu")
    menu.set_defaults(handler=lambda args: _run_menu())

    tokens = commands.add_parser(
        "tokens", parents=[language],
        help="list every token with its category, then totals per category",
        description="Show how the lexer splits code into tokens (8 categories, with totals).",
    )
    source = tokens.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?", help="source file to read (input mode 3)")
    source.add_argument("-l", "--line", metavar="CODE", help="one line of code (input mode 1)")
    source.add_argument("--stdin", action="store_true",
                        help="read a block of code from standard input (input mode 2)")
    tokens.set_defaults(handler=_run_tokens)
    return parser


# ---------------------------------------------------------------- commands

def _run_line(args: argparse.Namespace) -> int:
    return _report([require_code(from_text(args.code, name="<single line>"))], args)


def _run_block(args: argparse.Namespace) -> int:
    code = read_block(prompt=sys.stdin.isatty())
    return _report([require_code(from_text(code, name="<code block>"))], args)


def _run_files(args: argparse.Namespace) -> int:
    return _report([require_code(from_file(path)) for path in args.paths], args)


def _run_menu() -> int:
    from .menu import run_menu

    return run_menu()


def _run_tokens(args: argparse.Namespace) -> int:
    if args.line is not None:
        source = from_text(args.line, name="<single line>")
    elif args.stdin:
        source = from_text(sys.stdin.read(), name="<code block>")
    else:
        source = from_file(args.file)
    source = require_code(source)
    detection = detect_language(source, args.lang)
    print(format_token_listing(source, detection, tokenize(source, detection.profile)))
    return EXIT_OK


def _report(sources: list[Source], args: argparse.Namespace) -> int:
    """Analyze each source, then print or save the report(s)."""
    results = [analyze(source, args.lang) for source in sources]
    if args.fmt == "json":
        data = [to_dict(result) for result in results]
        text = json.dumps(data[0] if len(data) == 1 else data, indent=2, ensure_ascii=False)
    else:
        text = "\n\n".join(format_report(result, args.style) for result in results)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        failed = sum(1 for result in results if not result.passed)
        print(f"Report saved to {args.output} ({len(results)} analyzed, {failed} with errors).")
    elif args.fmt == "text" and enable_colors(sys.stdout, args.no_color):
        print(colorize(text))
    else:
        print(text)
    return EXIT_OK if all(result.passed for result in results) else EXIT_ERRORS_FOUND


def _never_crash_on_output() -> None:
    """Replace characters the console cannot display instead of crashing.

    A Windows console using an old code page cannot print every Unicode
    character, and printing one would normally raise UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
