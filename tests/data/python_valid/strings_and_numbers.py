# Every common way to write a string or a number.
single = 'single quotes'
double = "double quotes"
escaped = "tab\there, quote \" and backslash \\"
raw = r"C:\new\folder"
data = b"\x00\xff bytes"
raw_bytes = rb"\d+"
unicode_text = u"caf\u00e9"
formatted = f"{single!r} has {len(single)} characters"
formatted_spec = f"{3.14159:>10.2f}|{42:08b}"
nested = f"{'inner'} and {f'{1 + 1}'}"
doc = """A triple-quoted string
that spans "several" lines."""
also_doc = '''Single-quoted triple
string'''
joined = ("implicit " "concatenation "
          'across lines')
continued = "backslash \
continuation"

integers = [0, 7, 42, 1_000_000, 0x1F, 0XfF, 0o17, 0b1010, 0B1_0]
floats = [3.14, .5, 5., 1e10, 2.5E-3, 1_000.000_1, 6.02e+23]
complex_numbers = [3j, 1.5j, 2e3J]
