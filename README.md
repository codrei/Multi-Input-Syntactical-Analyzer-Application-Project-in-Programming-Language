# SyntaxLens — Multi-Input Syntactical Analyzer

[![CI](https://github.com/codrei/Multi-Input-Syntactical-Analyzer-Application-Project-in-Programming-Language/actions/workflows/ci.yml/badge.svg)](https://github.com/codrei/Multi-Input-Syntactical-Analyzer-Application-Project-in-Programming-Language/actions/workflows/ci.yml)

SyntaxLens checks source code for syntax errors without running it. Code can be
given three ways: a single line, a multi-line block, or an uploaded file.
SyntaxLens splits the code into tokens and checks them against syntax rules.
It then produces a report that either confirms the code is valid or lists each
error with its line number, category and explanation.

Languages: **Python** and **Java**, followed by C, C++, C# and JavaScript.

> **Status — Phase 1 of 8 complete.** Input loading, language detection and the
> lexer (tokenizer) for Python and Java are working and tested. The eight syntax
> checks are next. See the [progress checklist](#progress) and the full
> [project plan](docs/PLAN.md).

## Try it

You need Python 3.10 or newer. On Windows, install it from
[python.org](https://www.python.org/downloads/); the installer adds the `py`
command. The analysis engine needs no other packages.

```bat
git clone https://github.com/codrei/Multi-Input-Syntactical-Analyzer-Application-Project-in-Programming-Language.git syntaxlens
cd syntaxlens
py -m syntaxlens tokens samples\spec_example_1.py
```

On macOS or Linux, use `python3` instead of `py` and `/` instead of `\`.

The `tokens` command already accepts all three input modes:

| Input mode | Command |
|---|---|
| 1. Single line | `py -m syntaxlens tokens --line "y = 20 + * 5"` |
| 2. Code block | `py -m syntaxlens tokens --stdin`, paste the code, then press Ctrl+Z and Enter (Ctrl+D on macOS/Linux) |
| 3. File | `py -m syntaxlens tokens samples\HelloWorld.java` |

Output for Example 1 from the project specification:

```
============================================================
                LEXICAL ANALYSIS: TOKEN LIST
============================================================
Source: spec_example_1.py
Language: Python (auto-detected from the .py extension)
Total Lines: 3

   #  LINE:COL  CATEGORY              TOKEN
------------------------------------------------------------
   1  1:1       Identifier            x
   2  1:3       Operator              =
   3  1:5       Numeric Literal       10
   4  2:1       Keyword               if
   5  2:4       Delimiter             (
   6  2:5       Identifier            x
   7  2:7       Operator              >
   8  2:9       Numeric Literal       5
   9  2:10      Delimiter             )
  10  2:11      Delimiter             :
  11  3:5       Identifier            print
  12  3:10      Delimiter             (
  13  3:11      String/Char Literal   "Value is valid"
  14  3:27      Delimiter             )
------------------------------------------------------------
TOKEN SUMMARY BY CATEGORY:
  Keywords ...............   1  if
  Identifiers ............   3  x (x2), print
  Operators ..............   2  =, >
  Numeric Literals .......   2  10, 5
  String & Char Literals .   1  "Value is valid"
  Delimiters .............   5  ( (x2), ) (x2), :
  Comments ...............   0
  Invalid Tokens .........   0
  Total Tokens Parsed ....  14
============================================================
```

The total of 14 matches the "Total Tokens Parsed: 14" in the specification's
expected report.

On the specification's Example 2, the lexer already marks the unclosed string on
line 3 and continues reading line 4 normally:

```
  11  3:11      String/Char Literal   "Value is valid)   <-- literal is never closed
  12  4:1       Identifier            y
```

## How it works

SyntaxLens is a pipeline of small, independent stages:

```
 line / block / file
        │
  ① Source      decode, normalize line endings, reject blank / binary / oversized input   ✔ done
  ② Detect      choose the language: file extension, otherwise score the content          ✔ done
  ③ Lexer       one master regular expression → tokens in 8 categories                    ✔ done
  ④ Structurer  tokens → statements (Python: logical lines + indentation; C-style: ; { })
  ⑤ 8 Checks    independent modules; each error type belongs to exactly one check
  ⑥ Filter      keep root causes, drop follow-on errors
  ⑦ Report      one result object → text report / JSON / web UI
```

**The lexer** joins every token pattern of a language into one regular
expression and reads the input in a single left-to-right pass. Three rules make
it reliable:

- **Order matters:** comments and strings are matched before operators, and
  longer operators before shorter ones (`**=` before `**` before `*`).
- **Strings and comments are single tokens:** code-like text inside
  `"if (x > 0)"` is never checked as code.
- **It never stops:** an unclosed string ends at the end of its line, and an
  illegal character becomes an *invalid* token, so analysis always continues.

All language-specific details (keywords, operators, comment markers, string and
number formats) are stored as data in [`syntaxlens/profiles/`](syntaxlens/profiles),
so the lexer itself contains no language-specific code.

### The eight syntax checks (Phase 2)

| # | Check | Example errors |
|---|---|---|
| 1 | Delimiter & bracket matching | `if (x > 5` · `a[1)` · a stray `}` |
| 2 | String & character literals | `print("hi)` · `'ab'` as a Java char literal |
| 3 | Statement terminators | a missing `;` in Java · a missing `:` after a Python `if` |
| 4 | Operator syntax | `20 + * 5` · `x = 5 +` · `5 = x` |
| 5 | Control structure headers | `if :` · `for i range(10):` · `for (i=0, i<5, i++)` |
| 6 | Identifier naming | `2total = 5` · `my-var = 3` · `class = 5` |
| 7 | Indentation & block structure | an unexpected indent · `else` without `if` |
| 8 | Illegal characters & malformed literals | curly quotes “ ” pasted from Word · `3.14.15` |

## Progress

- [x] **Phase 1 — Foundation:** project setup, automated testing on Windows and Linux, input loading, language detection, Python and Java lexer, 8 token categories, `tokens` command
- [ ] **Phase 2 — Syntax checks:** statement builder, the 8 checks for Python and Java, error recovery; both specification examples reproduced
- [ ] **Phase 3 — More languages:** C, C++, C#, JavaScript; accuracy test sets
- [ ] **Phase 4 — Report and CLI:** the full report in the specification's format; `line`, `block` and `file` commands
- [ ] **Phase 5 — Web app:** three input tabs, highlighted errors, result tabs with visual counts
- [ ] **Phase 6 — Hardening:** robustness tests, Windows `.exe`, one-click launcher
- [ ] **Phase 7 — Documentation:** User Manual (PDF and DOCX)
- [ ] **Phase 8 — Demo:** demonstration video and defense preparation

## Testing

```bat
py -m pip install -e ".[dev]"
py -m pytest
```

The test suite has 138 tests. Highlights:

- Example 1 from the specification produces exactly 14 tokens with the expected category totals.
- On five sample programs, the Python lexer splits code token-for-token the same way as
  Python's own `tokenize` module.
- Windows line endings, byte-order marks, Windows-1252 files, and blank, binary and
  oversized files are all covered.

GitHub Actions runs the suite on Windows and Linux with Python 3.10–3.13 on every push.

## Repository layout

```
syntaxlens/        the analyzer
  source.py        ① input loading
  detect.py        ② language detection
  lexer.py         ③ tokenizer
  tokens.py        token kinds and the 8 categories
  profiles/        language rules stored as data (Python, Java)
  report/          text reports
  cli.py           command-line interface
tests/             automated tests (pytest)
samples/           demo inputs, including both specification examples
docs/PLAN.md       project plan and schedule
```
