"""Registry of the languages SyntaxLens can analyze."""

from .base import LanguageProfile
from .cfamily import CPP, CSHARP, JAVA, C
from .python import PYTHON

#: Every supported language, keyed by the id used on the command line and in the web app.
PROFILES: dict[str, LanguageProfile] = {
    profile.key: profile for profile in (PYTHON, JAVA, C, CPP, CSHARP)
}


def get_profile(key: str) -> LanguageProfile:
    """Look up a language by its id ("python", "java", "c", "cpp", "csharp")."""
    try:
        return PROFILES[key.lower()]
    except KeyError:
        choices = ", ".join(PROFILES)
        raise ValueError(f"Unsupported language '{key}'. Choose one of: {choices}.") from None


__all__ = ["C", "CPP", "CSHARP", "JAVA", "PROFILES", "PYTHON", "LanguageProfile", "get_profile"]
