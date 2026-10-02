import pytest

from syntaxlens.source import MAX_INPUT_BYTES, InputError, from_bytes, from_file, from_text


def test_windows_line_endings_are_normalized():
    source = from_bytes(b"x = 1\r\ny = 2\r\n", name="win.py")
    assert source.text == "x = 1\ny = 2\n"
    assert source.newline_style == "CRLF"
    assert source.lines == ("x = 1", "y = 2")


def test_mixed_line_endings_are_normalized():
    source = from_bytes(b"a\r\nb\rc\n")
    assert source.text == "a\nb\nc\n"
    assert source.newline_style == "mixed"


def test_single_line_has_no_line_ending():
    source = from_text("x = 10", name="<single line>")
    assert source.newline_style == "none"
    assert source.line_count == 1


@pytest.mark.parametrize(
    ("text", "count"),
    [("", 0), ("a", 1), ("a\n", 1), ("a\nb", 2), ("a\nb\n", 2), ("a\n\n", 2)],
)
def test_line_count_ignores_the_final_newline(text, count):
    assert from_text(text).line_count == count


def test_position_maps_offsets_to_lines_and_columns():
    source = from_text("ab\ncd\n")
    assert source.position(0) == (1, 1)
    assert source.position(1) == (1, 2)
    assert source.position(3) == (2, 1)
    assert source.position(4) == (2, 2)


def test_utf8_byte_order_mark_is_removed():
    source = from_bytes(b"\xef\xbb\xbfx = 1\n")
    assert source.text == "x = 1\n"
    assert source.encoding == "utf-8-sig"


def test_pasted_byte_order_mark_is_removed():
    assert from_text("\ufeffx = 1").text == "x = 1"


def test_utf16_file_with_bom_is_decoded():
    source = from_bytes("name = 'café'\n".encode("utf-16"))
    assert source.text == "name = 'café'\n"
    assert source.encoding == "utf-16"


def test_windows_1252_file_falls_back_from_utf8():
    source = from_bytes("name = 'café'\n".encode("cp1252"))
    assert source.text == "name = 'café'\n"
    assert source.encoding == "cp1252"


def test_binary_file_with_nul_bytes_is_rejected():
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(InputError, match="binary"):
        from_bytes(png_header, name="photo.png")


def test_text_made_of_control_characters_is_rejected():
    with pytest.raises(InputError, match="binary"):
        from_bytes(bytes(range(1, 32)) * 10, name="blob.dat")


def test_oversized_input_is_rejected():
    with pytest.raises(InputError, match="limit"):
        from_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    with pytest.raises(InputError, match="limit"):
        from_text("x" * (MAX_INPUT_BYTES + 1))


def test_blank_input_is_detected():
    assert from_text("  \n\t\n").is_blank
    assert from_text("").is_blank
    assert not from_text("x").is_blank


def test_missing_file_gives_a_friendly_error(tmp_path):
    with pytest.raises(InputError, match="File not found"):
        from_file(tmp_path / "missing.py")


def test_folder_is_not_a_file(tmp_path):
    with pytest.raises(InputError, match="Not a file"):
        from_file(tmp_path)


def test_file_is_read_as_bytes_and_named(tmp_path):
    path = tmp_path / "hello.py"
    path.write_bytes(b"print('hi')\r\n")
    source = from_file(path)
    assert source.name == "hello.py"
    assert source.text == "print('hi')\n"
