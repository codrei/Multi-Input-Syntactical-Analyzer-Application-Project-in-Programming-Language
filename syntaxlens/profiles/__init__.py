"""Registry of the languages SyntaxLens can analyze."""

from .base import LanguageProfile
from .cfamily import JAVA
from .python import PYTHON

#: Every supported language, keyed by the id used on the command line and in the web app.
PROFILES: dict[str, LanguageProfile] = {profile.key: profile for profile in (PYTHON, JAVA)}


def get_profile(key: str) -> LanguageProfile:
    """Look up a language by its id ("python", "java", ...)."""
    try:
        return PROFILES[key.lower()]
    except KeyError:
        choices = ", ".join(PROFILES)
        raise ValueError(f"Unsupported language '{key}'. Choose one of: {choices}.") from None


__all__ = ["JAVA", "PROFILES", "PYTHON", "LanguageProfile", "get_profile"]
