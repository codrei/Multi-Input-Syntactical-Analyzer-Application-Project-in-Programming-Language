# SyntaxLens — Project Plan

**Project:** Multi-Input Syntactical Analyzer Application (final project)
**Target submission and oral defense:** around **October 9, 2026** (to be confirmed)
**Current status:** see the [progress checklist in the README](../README.md#progress)

## 1. Goal

Build an application that performs static syntax analysis on source code. The
user gives it code in one of three ways: a single line, a multi-line block, or
an uploaded file. The application splits the code into tokens, checks the
tokens against syntax rules, and prints a structured report. The report either
confirms the code is valid or lists each syntax error with its line number,
category and explanation.

## 2. Key decisions

| Decision | Choice | Reason |
|---|---|---|
| Implementation language | Python 3.10+. The analysis engine uses only the standard library (`re`, `dataclasses`, `enum`) | Readable by every member; no third-party code hides how the analysis works |
| Interfaces | Web app (main interface) + command-line interface, both calling the same analysis function | The web app gives a tabbed UI with visual counts; the CLI shows the engine is independent of the interface |
| Languages analyzed | Python and Java in the most depth, then C, C++, C# and JavaScript through shared C-style rules. The language is detected automatically, with a manual override | The spec's own examples use Python (`x = 10`) and Java (`System.out.println("Hello");`). Supporting both families covers both halves of the terminator check: semicolons, and colons/indentation |
| Analysis approach | Hand-written pipeline: regex lexer → statement builder → 8 independent checks → error filter → report | A real compiler stops at the first error: Python's own parser reports only 1 of the 3 errors in the spec's Example 2. A hand-written pipeline can recover and report every root cause, and every part of it can be explained in the defense |
| Web stack | FastAPI backend + plain HTML/CSS/JavaScript + the CodeMirror editor, with every file stored in the repo | No build step; works without internet on the presentation laptop |
| Target platform | Windows first, tested on Windows and Linux on every push, plus a no-install Windows `.exe` | All team members use Windows; the defense runs on a team member's laptop |

## 3. Features

### 3.1 Input modes (all three required)

| Mode | Web app | Command line |
|---|---|---|
| 1. Single line | "Single Line" tab | `syntaxlens line "x = 10"` |
| 2. Code block | "Code Block" tab (editor with line numbers) | `syntaxlens block` |
| 3. File upload | "Upload File" tab (drag and drop or browse: .py .java .c .cpp .h .cs .js .txt) | `syntaxlens file path/to/code.java` |

### 3.2 Syntax checks

The spec requires at least 4 checks and lists 6. We implement all 6 plus 2 more:

| # | Check | Example errors |
|---|---|---|
| 1 | Delimiter & bracket matching | `if (x > 5` · `a[1)` · a stray `}` · a `{` that is never closed |
| 2 | String & character literals | `print("hi)` · `'ab'` or `''` as a Java char literal · an unclosed `"""` |
| 3 | Statement terminators | a missing `;` in Java/C/C++/C# (a warning in JavaScript) · a missing `:` after a Python `if/for/def/class` |
| 4 | Operator syntax | `20 + * 5` · `x = 5 +` · `x = 5 6` · `5 = x` |
| 5 | Control structure headers | `if :` · `for i range(10):` · Java `for (i=0, i<5, i++)` · `if x > 5 {` without parentheses · `case 1` without `:` |
| 6 | Identifier naming | `2total = 5` · `int 1st;` · `my-var = 3` · `class = 5` |
| 7 | Indentation & block structure | an unexpected indent · a missing indented block · `else` without `if` · `break` outside a loop |
| 8 | Illegal characters & malformed literals | curly quotes “ ” pasted from Word or a PDF · `3.14.15` · `0b102` · an unclosed `/* comment` |

Each error has a code (for example `E401`), a severity (error or warning), a
line and column, and a suggested fix.

### 3.3 Token categories

Every token is sorted into one of 8 categories, and the report shows detailed
lists with totals: Keywords, Identifiers, Operators, Numeric Literals, String &
Char Literals, Delimiters, Comments, Invalid Tokens. The totals add up to
"Total Tokens Parsed" (14 for the spec's Example 1).

### 3.4 Report

- **Classic style:** the exact layout and wording of the spec's two example reports.
- **Detailed style:** adds a caret under the error column, the error code, the
  suggested fix, and totals per category.
- Export as `.txt` or `.json`; print to PDF from the browser.

### 3.5 Error recovery

The analyzer never stops at the first error:

1. The lexer never stops: characters it does not recognize become "invalid"
   tokens, and lexing continues.
2. Checking restarts at every statement boundary.
3. When one mistake causes several symptoms on a line, only the root cause is
   reported. This is why the spec's Example 2 produces exactly 3 errors; a
   naive line-by-line checker would report about 6.

## 4. Architecture

```
 line / block / file
        │
  ① Source      decode, normalize line endings, reject blank / binary / oversized input
  ② Detect      choose the language: file extension, otherwise score the content
  ③ Lexer       one master regular expression → tokens in 8 categories
  ④ Structurer  tokens → statements (Python: logical lines + indentation; C-style: ; { })
  ⑤ 8 Checks    independent modules; each error type belongs to exactly one check
  ⑥ Filter      keep root causes, drop follow-on errors
  ⑦ Report      one result object → text report / JSON / web UI
```

Repository layout (target):

```
syntaxlens/            the analysis engine and its interfaces
  source.py            ① input loading
  detect.py            ② language detection
  lexer.py             ③ tokenizer
  tokens.py            token and category definitions
  profiles/            per-language rules stored as data (keywords, operators, literals)
  structure.py         ④ statement builder                      (Phase 2)
  checks/              ⑤ one module per syntax check              (Phase 2)
  analyzer.py          ⑥ pipeline and error filter                (Phase 2)
  report/              ⑦ text and JSON reports
  cli.py               command-line interface
  web/                 FastAPI server and static web UI           (Phase 5)
tests/                 automated tests (pytest)
samples/               demo input files
docs/                  plan, manual, architecture, grammar, error catalog
```

## 5. Testing and accuracy

- **Spec examples:** automated tests check that both example inputs from the
  spec produce the spec's reports.
- **Unit tests** for every module.
- **Lexer cross-check:** the Python tokenizer is compared token by token with
  CPython's own `tokenize` module on sample programs.
- **Valid-code set:** realistic programs in each language, confirmed valid by
  the real compilers. The analyzer must report zero errors on them.
- **Planted-error set:** a script inserts one known error at a known line many
  times. We measure precision and recall per category, which gives a measured
  error rate.
- **Robustness:** random input never crashes the analyzer, and a 10,000-line
  file is analyzed in under one second.
- **Continuous integration:** GitHub Actions runs every test on Windows and
  Linux with Python 3.10–3.13 on every push.

## 6. Deliverables

1. Source code repository with setup instructions, a one-click launcher and a Windows `.exe`
2. User Manual & System Documentation (3–5 pages, PDF and DOCX)
3. Demo video (3–5 minutes) showing all three input modes
4. Oral defense preparation: a guide answering the spec's sample questions, plus practice sessions

## 7. Work areas

| Area | Modules | Explains in the defense |
|---|---|---|
| A. Core engine | source, detect, lexer, profiles, pipeline, error filter, checks #2 and #8 | tokenization, token counting, language detection, error recovery |
| B. Structure checks | checks #1, #3, #7 | the bracket stack, nested brackets, missing-semicolon logic, indentation |
| C. Grammar checks | checks #4, #5, #6 | operator/operand logic, header grammars, identifier rules |
| D. Interfaces | report formatter, CLI, web app, exports, Windows build | the three input modes, file handling, the web API and UI |

Each member writes the tests for their area, prepares demo samples for it, and
implements at least one rule in it.

## 8. Schedule

| Date | Phase | Output |
|---|---|---|
| Tue Sep 29 | 1 | Project setup, CI, input loading, lexer for Python and Java, token categories |
| Wed Sep 30 | 2 | Statement builder, the 8 checks for Python and Java, error recovery; both spec examples pass |
| Thu Oct 1 | 3 | C, C++, C#, JavaScript; language auto-detection; accuracy test sets |
| Fri Oct 2 | 4 | Report formatter and CLI (all three input modes) |
| Sat Oct 3 | 5 | Web app |
| Sun Oct 4 | 6 | Hardening, Windows `.exe`, one-click launcher; **code freeze**; test run on the presentation laptop |
| Mon Oct 5 | 7 | README, User Manual (PDF + DOCX), technical documentation |
| Tue Oct 6 | 8 | Demo video |
| Oct 7–8 | — | Defense practice |
| ~Oct 9 | — | Submission and oral defense (date to be confirmed) |

## 9. Risks

| Risk | Mitigation |
|---|---|
| False errors on valid code | Zero-error requirement on the valid-code set, checked on every push. A construct the analyzer does not understand is not flagged |
| The presentation laptop fails on the day | No-install `.exe`; all web files bundled (no internet needed); test run on Oct 4; the CLI and the recorded video as backups |
| Six languages is a wide scope | Python and Java are completed first; the depth of the other languages is the first thing reduced if time runs short |
