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
