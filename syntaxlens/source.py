"""Input loading: turns whatever the user gives us into clean, uniform text.

All three input modes pass through this module:

* Mode 1 (single line) and Mode 2 (code block) arrive as text (``str``).
* Mode 3 (file upload) arrives as raw ``bytes`` that must be decoded first.

Either way the result is a :class:`Source`.  Its ``text`` always uses ``\\n``
line endings, whatever the input originally used (Windows ``\\r\\n``, old Mac
``\\r`` or Linux ``\\n``), so no later stage has to think about line endings.

Input that cannot be analyzed (a binary file such as an image, a missing
path, or a file above the size limit) raises :class:`InputError`.  Its message
is written for end users, so the command line and web app can show it as-is.
"""

from __future__ import annotations

import bisect
import codecs
from dataclasses import dataclass, field
from pathlib import Path

#: Largest input accepted: 2 MB, far above any hand-written program.
MAX_INPUT_BYTES = 2 * 1024 * 1024

#: How many leading bytes are inspected to decide whether a file is binary.
_SNIFF_SIZE = 8192

#: Byte-order marks (BOMs) identify an encoding with certainty.  UTF-32 must be
#: tested before UTF-16 because the UTF-32 LE mark begins with the UTF-16 LE one.
_BOMS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


class InputError(ValueError):
    """The input cannot be analyzed.  The message is safe to show to users."""


@dataclass(frozen=True)
class Source:
    """Normalized source text, plus the facts later stages need about it."""

    text: str                    # the code, with "\n" line endings only
    name: str = "<input>"        # file name, or a label such as "<single line>"
    encoding: str = "utf-8"      # how the original bytes were decoded
    newline_style: str = "LF"    # original line endings: LF, CRLF, CR, mixed or none
    lines: tuple[str, ...] = field(default=(), init=False, repr=False, compare=False)
    _line_starts: tuple[int, ...] = field(default=(), init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # A frozen dataclass forbids normal attribute assignment, hence object.__setattr__.
        pieces = self.text.split("\n")
        starts = [0]
        for piece in pieces[:-1]:
            starts.append(starts[-1] + len(piece) + 1)  # +1 for the "\n" itself
        if pieces[-1] == "":
            pieces.pop()  # a final "\n" ends the last line; it does not start a new one
        object.__setattr__(self, "lines", tuple(pieces))
        object.__setattr__(self, "_line_starts", tuple(starts))

    @property
    def line_count(self) -> int:
        """Number of physical lines in the input."""
        return len(self.lines)

    @property
    def is_blank(self) -> bool:
        """True when the input contains nothing but whitespace."""
        return not self.text.strip()

    def line_text(self, line: int) -> str:
        """Text of one line, numbered from 1 (empty for numbers out of range)."""
        return self.lines[line - 1] if 1 <= line <= len(self.lines) else ""

    def position(self, offset: int) -> tuple[int, int]:
        """Convert a character offset in ``text`` into (line, column), both counted from 1.

        ``_line_starts`` holds the offset where every line begins, in increasing
        order, so a binary search finds the line in O(log n) steps.
        """
        index = bisect.bisect_right(self._line_starts, offset) - 1
        return index + 1, offset - self._line_starts[index] + 1


def from_text(text: str, name: str = "<input>") -> Source:
    """Prepare code that was typed or pasted (input modes 1 and 2)."""
    size = len(text.encode("utf-8", errors="replace"))
    if size > MAX_INPUT_BYTES:
        raise InputError(f"The input is {_size(size)}; the limit is {_size(MAX_INPUT_BYTES)}.")
    text = text.removeprefix("﻿")  # a byte-order mark copied along with the code
    text, style = _normalize_newlines(text)
    return Source(text=text, name=name, newline_style=style)


def from_bytes(data: bytes, name: str = "<file>") -> Source:
    """Prepare the raw contents of an uploaded or opened file (input mode 3)."""
    if len(data) > MAX_INPUT_BYTES:
        raise InputError(f"'{name}' is {_size(len(data))}; the limit is {_size(MAX_INPUT_BYTES)}.")
    text, encoding = _decode(data, name)
    text, style = _normalize_newlines(text)
    return Source(text=text, name=name, encoding=encoding, newline_style=style)


def from_file(path: str | Path) -> Source:
    """Read a source file from disk (input mode 3 on the command line)."""
    path = Path(path)
    if not path.exists():
        raise InputError(f"File not found: {path}")
    if not path.is_file():
        raise InputError(f"Not a file: {path}")
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:  # checked before reading, so huge files are never loaded
        raise InputError(f"'{path.name}' is {_size(size)}; the limit is {_size(MAX_INPUT_BYTES)}.")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise InputError(f"Could not read {path}: {error.strerror}") from error
    return from_bytes(data, name=path.name)


def _decode(data: bytes, name: str) -> tuple[str, str]:
    """Turn file bytes into text, choosing the encoding and rejecting binary files.

    1. A byte-order mark names the encoding outright.
    2. A NUL byte never appears in source code, but is common in binary files.
    3. Otherwise try UTF-8 (the modern default), then Windows-1252 (what Notepad
       saves as "ANSI"), then Latin-1, which accepts any byte sequence.
    4. Text that is mostly control characters is binary data in disguise.
    """
    for bom, encoding in _BOMS:
        if data.startswith(bom):
            return data.decode(encoding, errors="replace"), encoding
    if b"\x00" in data[:_SNIFF_SIZE]:
        raise InputError(_binary_message(name))
    for encoding in ("utf-8", "cp1252"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text, encoding = data.decode("latin-1"), "latin-1"
    if _mostly_control_characters(text[:_SNIFF_SIZE]):
        raise InputError(_binary_message(name))
    return text, encoding


def _mostly_control_characters(sample: str) -> bool:
    """True when over 10% of the characters are invisible control codes."""
    if not sample:
        return False
    controls = sum(1 for ch in sample if (ord(ch) < 32 and ch not in "\t\n\r\f\v") or ch == "\x7f")
    return controls / len(sample) > 0.10


def _normalize_newlines(text: str) -> tuple[str, str]:
    """Convert every line ending to "\\n" and report which style the input used."""
    crlf = text.count("\r\n")
    lone_cr = text.count("\r") - crlf
    lone_lf = text.count("\n") - crlf
    found = [style for style, count in (("CRLF", crlf), ("CR", lone_cr), ("LF", lone_lf)) if count]
    style = found[0] if len(found) == 1 else ("mixed" if found else "none")
    return text.replace("\r\n", "\n").replace("\r", "\n"), style


def _binary_message(name: str) -> str:
    return (
        f"'{name}' looks like a binary file (for example an image or a compiled program), "
        "not source code. Please choose a text file such as .py, .java or .txt."
    )


def _size(size: int) -> str:
    """Human-readable file size."""
    return f"{size / (1024 * 1024):.1f} MB" if size >= 1024 * 1024 else f"{size / 1024:.1f} KB"
