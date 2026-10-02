from pathlib import Path

import pytest

from syntaxlens.detect import detect_language
from syntaxlens.source import from_file, from_text

SAMPLES = Path(__file__).parent.parent / "samples"


def detect(code, name="<input>", requested="auto"):
    return detect_language(from_text(code, name=name), requested)


def test_user_choice_wins():
    detection = detect("def f():\n    pass\n", requested="java")
    assert (detection.profile.key, detection.method) == ("java", "selected")


def test_extension_wins_over_content():
    detection = detect("x = 10", name="Main.java")
    assert (detection.profile.key, detection.method) == ("java", "extension")
    assert detection.description == "Java (auto-detected from the .java extension)"


def test_bare_assignment_defaults_to_python():
    detection = detect("x = 10")
    assert (detection.profile.key, detection.method) == ("python", "default")


@pytest.mark.parametrize(
    "code",
    ['System.out.println("Hello");', "int total = 0;", "public class A {\n}"],
)
def test_java_snippets(code):
    assert detect(code).profile.key == "java"


@pytest.mark.parametrize(
    "code",
    ['x = 10\nif (x > 5):\n    print("Value is valid")\n', "def area(r):\n    return r * r\n",
     "import math\nprint(math.pi)\n"],
)
def test_python_snippets(code):
    assert detect(code).profile.key == "python"


def test_txt_file_is_scored_by_content(tmp_path):
    path = tmp_path / "snippet.txt"
    path.write_text((SAMPLES / "HelloWorld.java").read_text(encoding="utf-8"), encoding="utf-8")
    detection = detect_language(from_file(path))
    assert (detection.profile.key, detection.method) == ("java", "content")


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError, match="Unsupported language"):
        detect("x = 1", requested="cobol")
