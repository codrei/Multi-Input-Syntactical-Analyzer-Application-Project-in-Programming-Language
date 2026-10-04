import subprocess
import sys
from pathlib import Path

from syntaxlens.cli import EXIT_BAD_INPUT, EXIT_OK, main

SAMPLES = Path(__file__).parent.parent / "samples"


def test_tokens_for_spec_example_1(capsys):
    assert main(["tokens", str(SAMPLES / "spec_example_1.py")]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Total Tokens Parsed ....  14" in out
    assert "Python (auto-detected from the .py extension)" in out


def test_tokens_flags_the_unclosed_string_in_spec_example_2(capsys):
    assert main(["tokens", str(SAMPLES / "spec_example_2.py")]) == EXIT_OK
    out = capsys.readouterr().out
    assert '"Value is valid)   <-- literal is never closed' in out


def test_tokens_single_line_mode(capsys):
    assert main(["tokens", "--line", "y = 20 + * 5"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Source: <single line>" in out
    assert "Operators ..............   3  =, +, *" in out


def test_tokens_block_mode_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("int x = 5;\nx++;\n"))
    assert main(["tokens", "--stdin"]) == EXIT_OK
    assert "Java (auto-detected from the code)" in capsys.readouterr().out


def test_java_file(capsys):
    assert main(["tokens", str(SAMPLES / "HelloWorld.java")]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Invalid Tokens .........   0" in out


def test_missing_file(capsys):
    assert main(["tokens", "does_not_exist.py"]) == EXIT_BAD_INPUT
    assert "File not found" in capsys.readouterr().err


def test_blank_file(tmp_path, capsys):
    path = tmp_path / "empty.py"
    path.write_text("  \n\n", encoding="utf-8")
    assert main(["tokens", str(path)]) == EXIT_BAD_INPUT
    assert "empty" in capsys.readouterr().err


def test_binary_file(tmp_path, capsys):
    path = tmp_path / "image.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    assert main(["tokens", str(path)]) == EXIT_BAD_INPUT
    assert "binary" in capsys.readouterr().err


def test_no_command_prints_help(capsys):
    assert main([]) == EXIT_OK
    assert "tokens" in capsys.readouterr().out


def test_runs_as_python_dash_m():
    result = subprocess.run(
        [sys.executable, "-m", "syntaxlens", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert result.stdout.startswith("SyntaxLens ")


def test_file_mode_reports_errors_with_exit_code_1(capsys):
    assert main(["file", str(SAMPLES / "spec_example_2.py")]) == 1
    out = capsys.readouterr().out
    assert "Status: FAILED (3 Syntax Errors Detected)" in out


def test_file_mode_valid_code_exits_0(capsys):
    assert main(["file", str(SAMPLES / "spec_example_1.py")]) == 0
    assert "Syntax Validation: SUCCESSFUL" in capsys.readouterr().out


def test_line_mode(capsys):
    assert main(["line", "y = 20 + * 5"]) == 1
    out = capsys.readouterr().out
    assert "Category: Invalid Operator Sequence" in out
    assert main(["line", 'System.out.println("Hello");']) == 0
    assert "Java (auto-detected from the code)" in capsys.readouterr().out


def test_block_mode_stops_at_a_lone_dot(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("x = 10\nif x > 5\n    print(x)\n.\nignored(\n"))
    assert main(["block"]) == 1
    out = capsys.readouterr().out
    assert "Missing colon ':'" in out
    assert "Total Lines Analyzed: 3" in out


def test_language_can_be_forced(capsys):
    assert main(["line", "x = 10", "--lang", "java"]) == 1
    assert "Missing semicolon" in capsys.readouterr().out


def test_detailed_style_is_the_default(capsys):
    main(["file", str(SAMPLES / "spec_example_2.py")])
    out = capsys.readouterr().out
    assert "  - Fix: Add the missing ')'." in out
    assert "ERRORS BY CATEGORY (the 8 syntax checks):" in out


def test_classic_style_matches_the_specification(capsys):
    from tests.test_spec_examples import EXAMPLE_2_REPORT

    main(["file", str(SAMPLES / "spec_example_2.py"), "--style", "classic"])
    assert capsys.readouterr().out == EXAMPLE_2_REPORT + "\n"


def test_json_format(capsys):
    import json

    assert main(["line", "x = 5 +", "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["diagnostics"][0]["code"] == "E402"


def test_several_files_and_exit_code(capsys):
    files = [str(SAMPLES / "spec_example_1.py"), str(SAMPLES / "HelloWorld.java")]
    assert main(["file", *files]) == 0
    assert capsys.readouterr().out.count("SYNTACTICAL ANALYSIS REPORT") == 2
    assert main(["file", *files, str(SAMPLES / "spec_example_2.py")]) == 1


def test_output_file(tmp_path, capsys):
    target = tmp_path / "report.txt"
    assert main(["file", str(SAMPLES / "spec_example_2.py"), "--output", str(target)]) == 1
    assert "Report saved to" in capsys.readouterr().out
    saved = target.read_text(encoding="utf-8")
    assert saved.startswith("====")
    assert "\033[" not in saved                       # no color codes in files
