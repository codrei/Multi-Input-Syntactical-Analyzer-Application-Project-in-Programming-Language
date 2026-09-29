import re

import syntaxlens


def test_version_is_semantic():
    assert re.fullmatch(r"\d+\.\d+\.\d+", syntaxlens.__version__)
