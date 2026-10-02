"""Choosing which language's rules to apply.

Three kinds of evidence are used, strongest first:

1. **The user's choice**, e.g. ``--lang java`` or the web app's language menu.
2. **The file extension**: ``.py`` means Python, ``.java`` means Java.
3. **The code itself**, for pasted code and ``.txt`` files.  Each language has a
   list of regular expressions for features typical of it, each with a weight:
   ``def name(...):`` for Python, ``System.out.println(`` or a line ending in
   ``;`` for Java.  Every match adds its weight to that language's score, and
   the highest score wins.  With no evidence at all (e.g. ``x = 10``) the
   default is Python, the language of the spec's own examples.

More languages are added in Phase 3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePath

from .profiles import PROFILES, LanguageProfile, get_profile
from .source import Source

#: File extension -> language id.
EXTENSIONS = {
    extension: profile.key for profile in PROFILES.values() for extension in profile.extensions
}

DEFAULT_LANGUAGE = "python"

#: A match counts at most this many times, so one very repetitive feature
#: (hundreds of lines ending in ";") cannot outweigh everything else.
_MAX_HITS = 5


def _features(*pairs: tuple[int, str]) -> list[tuple[int, re.Pattern[str]]]:
    return [(weight, re.compile(pattern, re.MULTILINE)) for weight, pattern in pairs]


#: language id -> [(weight, pattern)], the evidence used to score pasted code.
FEATURES = {
    "python": _features(
        (4, r"^\s*def\s+\w+\s*\(.*\)\s*(->\s*[^:]+)?:\s*(#.*)?$"),     # def area(r):
        (3, r"^\s*elif\b"),                                             # elif x > 5:
        (2, r"^\s*(if|while|for|with|try|except|else|finally|class)\b[^;{]*:\s*(#.*)?$"),
        (2, r"^\s*(from\s+[\w.]+\s+import\s|import\s+[\w.]+\s*$)"),    # import math
        (2, r"\b(None|True|False|self|lambda|nonlocal)\b"),
        (1, r"(?<![.\w])print\s*\("),                                   # print( not after a dot
        (1, r"^\s*#\s"),                                                # # a comment
    ),
    "java": _features(
        (5, r"\bSystem\.(out|err)\.print(ln|f)?\s*\("),                 # System.out.println(
        (4, r"\b(public|private|protected)\s+(static\s+)?(final\s+)?"
            r"(class|interface|enum|void|int|String|boolean|double)\b"),
        (4, r"^\s*import\s+java\."),
        (3, r"\bString\s*\[\s*\]\s+\w+"),                              # String[] args
        (2, r"\bnew\s+[A-Z]\w*\s*[(<\[]"),                              # new Scanner(
        (2, r"^\s*(int|double|float|long|short|byte|char|boolean|String)\s+\w+\s*[=;,]"),
        (1, r";\s*(//.*)?$"),                                           # a line ending in ;
        (1, r"[{}]\s*$"),                                               # a line ending in { or }
    ),
}


@dataclass(frozen=True)
class Detection:
    """The chosen language and why it was chosen."""

    profile: LanguageProfile
    method: str   # "selected", "extension", "content" or "default"
    reason: str   # e.g. "auto-detected from the .py extension"

    @property
    def description(self) -> str:
        """For reports, e.g. 'Python (auto-detected from the .py extension)'."""
        return f"{self.profile.name} ({self.reason})"


def detect_language(source: Source, requested: str = "auto") -> Detection:
    """Decide which language rules to apply to ``source``."""
    if requested and requested.lower() != "auto":
        return Detection(get_profile(requested), "selected", "selected by the user")

    extension = PurePath(source.name).suffix.lower()
    if extension in EXTENSIONS:
        profile = get_profile(EXTENSIONS[extension])
        return Detection(profile, "extension", f"auto-detected from the {extension} extension")

    scores = score_languages(source.text)
    best = max(scores, key=lambda key: (scores[key], key == DEFAULT_LANGUAGE))
    if scores[best] == 0:
        reason = "default: no language-specific features found"
        return Detection(get_profile(DEFAULT_LANGUAGE), "default", reason)
    return Detection(get_profile(best), "content", "auto-detected from the code")


def score_languages(text: str) -> dict[str, int]:
    """Score how strongly ``text`` resembles each language (higher is stronger)."""
    return {
        language: sum(
            weight * min(len(pattern.findall(text)), _MAX_HITS) for weight, pattern in features
        )
        for language, features in FEATURES.items()
    }
