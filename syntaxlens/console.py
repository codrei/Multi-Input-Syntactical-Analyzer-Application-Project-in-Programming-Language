"""Colors for the terminal.

The report text itself is plain; color is added afterwards, line by line, only
when the output is a terminal.  Saved files and piped output stay plain text.

Colors use ANSI escape codes.  Windows 10 and later understand them once
"virtual terminal processing" is switched on for the console, which
:func:`enable_colors` does.  Set the NO_COLOR environment variable (a common
convention) or pass --no-color to turn colors off.
"""

from __future__ import annotations

import os
import re
import sys
from typing import TextIO

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"

#: (pattern, style) pairs applied to report lines; the first match wins.
_RULES = [
    (re.compile(r"^Status: PASSED.*"), BOLD + GREEN),
    (re.compile(r"^Status: FAILED.*"), BOLD + RED),
    (re.compile(r"^\[ERROR \d+\].*"), BOLD + RED),
    (re.compile(r"^\[WARNING \d+\].*"), BOLD + YELLOW),
    (re.compile(r"^\s+\|\s*\^$"), RED),                         # the caret under the column
    (re.compile(r"^  - Fix: .*"), GREEN),
    (re.compile(r"^  - Syntax Check: .*-> ERROR.*"), RED),
    (re.compile(r"^  - Syntax Check: .*-> WARNING.*"), YELLOW),
    (re.compile(r"^  - Syntax Validation: SUCCESSFUL"), GREEN),
    (re.compile(r"^[A-Z][A-Z &()0-9'-]+:$|^[A-Z][A-Z &]+ \(.*\):$"), BOLD + CYAN),  # section titles
    (re.compile(r"^[=-]{20,}$"), DIM),
]


def enable_colors(stream: TextIO = sys.stdout, disabled: bool = False) -> bool:
    """Decide whether to color output on ``stream``, preparing Windows if needed."""
    if disabled or "NO_COLOR" in os.environ or not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)                 # the standard output console
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))  # virtual terminal
    except (AttributeError, OSError):
        return False


def colorize(text: str) -> str:
    """Add colors to a report, one line at a time."""
    out = []
    for line in text.split("\n"):
        for pattern, style in _RULES:
            if pattern.match(line):
                line = f"{style}{line}{RESET}"
                break
        out.append(line)
    return "\n".join(out)
