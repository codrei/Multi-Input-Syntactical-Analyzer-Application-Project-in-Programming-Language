"""The interactive menu, driven by a scripted list of answers."""

from pathlib import Path

from syntaxlens.menu import run_menu

SAMPLES = Path(__file__).parent.parent / "samples"


def drive(*answers):
    """Run the menu with these answers; return everything it showed."""
    pending = list(answers)
    shown = []

    def ask(prompt):
        shown.append(prompt)
        if not pending:
            raise EOFError
        return pending.pop(0)

    assert run_menu(ask=ask, show=shown.append) == 0
    return "\n".join(shown)


def test_single_line_mode():
    out = drive("1", "y = 20 + * 5", "", "0")
    assert "Consecutive binary operators '+ *'" in out
    assert "Goodbye!" in out


def test_code_block_mode_ends_at_a_dot():
    out = drive("2", "x = 10", "if (x > 5):", '    print("Value is valid")', ".", "", "0")
    assert "Status: PASSED (0 Syntax Errors Found)" in out
    assert "Total Lines Analyzed: 3" in out


def test_file_mode_accepts_a_quoted_windows_path():
    out = drive("3", f'"{SAMPLES / "spec_example_2.py"}"', "", "0")
    assert "Status: FAILED (3 Syntax Errors Detected)" in out


def test_missing_file_is_explained_not_fatal():
    out = drive("3", "no_such_file.py", "0")
    assert "Cannot analyze this input: File not found" in out


def test_settings_change_language_and_style():
    out = drive("4", "3", "2", "1", "x = 10", "", "0")
    assert "Settings saved: language java, report classic." in out
    assert "Target Syntax Rule: Java (selected by the user)" in out
    assert "ERRORS BY CATEGORY" not in out          # classic style


def test_help_and_unknown_choices():
    out = drive("5", "9", "0")
    assert "SyntaxLens checks code for syntax errors" in out
    assert "Please choose 0, 1, 2, 3, 4 or 5." in out


def test_end_of_input_exits_cleanly():
    assert "Goodbye!" in drive()
