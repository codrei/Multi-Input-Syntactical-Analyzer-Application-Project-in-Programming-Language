"""Interactive menu, shown when ``syntaxlens`` is run with no command.

It offers the three input modes by number, so nobody has to remember the
command-line syntax:

    1  Single line   - type one statement
    2  Code block    - type or paste several lines, end with a line holding '.'
    3  File          - give the path of a source file
    4  Settings      - choose the language rules and the report style
    5  Help
    0  Exit

On Windows, "Copy as path" in File Explorer puts quotes around the path; the
quotes are removed automatically.
"""

from __future__ import annotations

from collections.abc import Callable

from .analyzer import analyze
from .cli import BLOCK_END_MARKER, render, require_code
from .console import colorize, enable_colors
from .profiles import PROFILES
from .report.text import HEAVY_RULE, STYLES
from .source import InputError, from_file, from_text

BANNER = """\
============================================================
        SyntaxLens - Multi-Input Syntactical Analyzer
============================================================"""

HELP = """\
SyntaxLens checks code for syntax errors without running it.

  1  Single line  analyzes one statement, e.g.  x = 10  or  System.out.println("Hi");
  2  Code block   analyzes several lines. Paste them, then type a line with only '.'
  3  File         analyzes a whole file (.py, .java, .txt, ...). Give its path, e.g.
                  samples\\spec_example_2.py   (quotes around the path are fine)

The language is detected automatically; choose it in Settings if detection guesses
wrong. The 'detailed' report adds error codes, column pointers, fixes and totals per
category; 'classic' is the exact layout of the specification's examples."""


def run_menu(ask: Callable[[str], str] = input, show: Callable[[str], None] = print) -> int:
    """Run the menu until the user exits.  ``ask`` and ``show`` can be replaced in tests."""
    colors = enable_colors() if show is print else False
    settings = {"lang": "auto", "style": "detailed"}

    def prompt(text: str) -> str | None:
        try:
            return ask(text)
        except (EOFError, KeyboardInterrupt):
            return None

    show(BANNER)
    while True:
        show("")
        show(f"  1  Single line      2  Code block      3  File\n"
             f"  4  Settings (language: {settings['lang']}, report: {settings['style']})\n"
             f"  5  Help             0  Exit")
        choice = prompt("Choose an option: ")
        if choice is None or choice.strip().lower() in ("0", "q", "quit", "exit"):
            show("Goodbye!")
            return 0
        choice = choice.strip()
        try:
            if choice == "1":
                code = prompt("Enter one line of code: ")
                if code is None:
                    continue
                source = from_text(code, name="<single line>")
            elif choice == "2":
                show(f"Type or paste your code. End with a line containing only '{BLOCK_END_MARKER}'.")
                lines = []
                while (line := prompt("")) is not None and line != BLOCK_END_MARKER:
                    lines.append(line)
                source = from_text("\n".join(lines), name="<code block>")
            elif choice == "3":
                path = prompt("Path to the file: ")
                if path is None:
                    continue
                source = from_file(path.strip().strip('"').strip("'"))
            elif choice == "4":
                _settings(settings, prompt, show)
                continue
            elif choice == "5":
                show(HELP)
                continue
            else:
                show("Please choose 0, 1, 2, 3, 4 or 5.")
                continue
            result = analyze(require_code(source), settings["lang"])
        except InputError as error:
            show(f"Cannot analyze this input: {error}")
            continue
        report = render(result, settings["style"])
        show(colorize(report) if colors else report)
        prompt("Press Enter to return to the menu...")


def _settings(settings: dict, prompt, show) -> None:
    languages = ["auto", *PROFILES]
    show("Language rules:")
    for number, language in enumerate(languages, start=1):
        show(f"  {number}  {language}")
    choice = prompt(f"Choose 1-{len(languages)} (Enter keeps '{settings['lang']}'): ")
    if choice and choice.strip().isdigit() and 1 <= int(choice) <= len(languages):
        settings["lang"] = languages[int(choice) - 1]
    show("Report style:")
    for number, style in enumerate(STYLES, start=1):
        show(f"  {number}  {style}")
    choice = prompt(f"Choose 1-{len(STYLES)} (Enter keeps '{settings['style']}'): ")
    if choice and choice.strip().isdigit() and 1 <= int(choice) <= len(STYLES):
        settings["style"] = STYLES[int(choice) - 1]
    show(f"Settings saved: language {settings['lang']}, report {settings['style']}.")
    show(HEAVY_RULE)
