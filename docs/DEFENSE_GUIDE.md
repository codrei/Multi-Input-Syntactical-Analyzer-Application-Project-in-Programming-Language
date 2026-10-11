# SyntaxLens: Oral Defense Guide

**Defense:** October 13, 2026 · 10–15 minutes · **25% of the grade, scored per person.**
Every member must answer technical questions about the code. The panel may ask the
questions from section 6 of the specification; all of them are answered below.

How to use this guide:

1. Read section 1 to see which part you present.
2. Read **your** answers in section 4 out loud until you can say them without the page.
3. Open the files linked next to your answers and follow the code with your finger.
4. Practice the demo (section 3) once on the presentation laptop.

---

## 1. Who presents what

The split follows who built each area. Each member owns one or two of the
specification's questions plus their own walkthrough (question 8).

| Member | Area | Files to know | Questions |
|---|---|---|---|
| **Marco Andrei R. Belen** | The pipeline: tokenizer, statement builder, error recovery | [`lexer.py`](../syntaxlens/lexer.py), [`structure.py`](../syntaxlens/structure.py), [`analyzer.py`](../syntaxlens/analyzer.py) | Q1 tokenizing · Q7 recovery |
| **Gabriel M. Caporado** | Language rules and the operator check | [`profiles/rules.py`](../syntaxlens/profiles/rules.py), [`expressions.py`](../syntaxlens/expressions.py), [`checks/operators.py`](../syntaxlens/checks/operators.py) | Q3 `+5` vs `+ *` |
| **Ariz Luiz L. Guillarte** | C, C++ and C# profiles, strings, brackets | [`profiles/cfamily.py`](../syntaxlens/profiles/cfamily.py), [`checks/delimiters.py`](../syntaxlens/checks/delimiters.py), [`lexer.py`](../syntaxlens/lexer.py) (`_literal_patterns`) | Q2 bracket stack · Q6 strings |
| **Brix Martin M. Paña** | Input handling, the web app and the live demo | [`source.py`](../syntaxlens/source.py), [`web/app.py`](../syntaxlens/web/app.py), [`cli.py`](../syntaxlens/cli.py), [`report/text.py`](../syntaxlens/report/text.py) | Q4 line breaks, tabs, comments · Q5 blank and binary files |

**Suggested running order (about 12 minutes):**

| Time | Who | What |
|---|---|---|
| 1 min | Marco | What SyntaxLens does, and the 7-stage pipeline (section 2 of the User Manual) |
| 4 min | Brix | Live demo of the three input modes (section 3 below) |
| 2 min | Marco | How code becomes tokens, and how the analyzer keeps going after an error |
| 2 min | Ariz | The bracket stack, and why code inside strings is never checked |
| 2 min | Gabriel | The operator state machine, and how one engine supports five languages |
| rest | All | Questions |

---

## 2. Before the defense

**On the presentation laptop (do this on October 12, not on the day):**

- [ ] Python 3.10 or newer is installed, with "Add python.exe to PATH" ticked.
      Check in a Command Prompt: `py --version`.
- [ ] The project is on the laptop (GitHub → Code → Download ZIP, then extract it).
- [ ] Double-click `run.bat`. The browser opens the app at `http://127.0.0.1:8000`.
      Keep the black console window open while presenting.
- [ ] The **Load a sample** menu shows the samples, and Spec Example 2 gives 3 errors.
- [ ] Create an **empty** text file on the Desktop (`empty.txt`) for the blank-file demo.
- [ ] Open the online app as a backup: <https://multi-input-syntactical-analyzer-ap.vercel.app>.
- [ ] Open a Command Prompt in the project folder for the command-line demo.
- [ ] Each member: open your files in VS Code in separate tabs.
- [ ] Turn off sleep, notifications and auto-updates. Bring the charger.

**Numbers to remember:**

| | |
|---|---|
| Input modes | 3: single line, code block, file upload (web app and command line) |
| Syntax checks | 8: the 6 in the specification + indentation/blocks + illegal characters |
| Token categories | 8: keywords, identifiers, operators, numbers, strings & chars, delimiters, comments, invalid |
| Languages | 5: Python, Java, C, C++, C# |
| Spec Example 1 | PASSED, exactly **14 tokens** |
| Spec Example 2 | exactly **3 errors** (lines 2, 3, 4); Python's own parser finds only 1 |
| Tests | **606**, on Windows and Linux, Python 3.10–3.14, on every push |
| False alarms | **0** on 19 realistic valid programs |
| Catch rate | **98.3%** of 1,601 planted mistakes reported on the right line |
| Speed | 10,000 lines in under half a second |
| Libraries | Python standard library only (`re`, `dataclasses`, `enum`, `wsgiref`); CodeMirror for the editor |

---

## 3. Live demo script (Brix)

Use the web app. Say one sentence before each step: what you are about to show.

1. **Mode 1, Single Line.** Click the example chip `y = 20 + * 5` and press Enter.
   → FAILED, "Consecutive binary operators '+ *'". Then type `x = +5`.
   → PASSED: a `+` before a value is a sign, not an error (Gabriel explains why).
2. **Mode 2, Code Block.** *Load a sample* → **Spec Example 2 - three errors** → Analyze.
   → Exactly the specification's three errors. Open the **Report** tab, choose
   **Classic (spec format)**: it matches the specification word for word.
   Load **Spec Example 1** → PASSED, *Total Tokens Parsed: 14*.
3. **Mode 3, Upload File.** Drag `samples/ErrorsDemo.java` (or `samples/errors_demo.c`)
   onto the box. → 10 errors. Click an error: the editor jumps to its line.
   Open the **Tokens** tab and filter by a category.
4. **Edge cases.** Upload `docs/images/web-app.png` → "looks like a binary file ...
   not source code". Upload `empty.txt` → "is empty: there is no code to analyze".
5. **Command line (if time allows).** In the Command Prompt:

   ```bat
   py -m syntaxlens line "y = 20 + * 5"
   py -m syntaxlens file samples\spec_example_2.py --style classic
   ```

**If something goes wrong:** switch to the online app; if there is no internet,
use the command line; if Python itself fails, show the online app on a phone.

---

## 4. The specification's questions

Each answer has: **who** answers, **what to say** (about 30–60 seconds), **what
to show**, and **likely follow-ups**.

### Q1. "How does your application tokenize input text before checking for syntax errors?"

**Who:** Marco

**Say:**
> Before any check runs, the lexer turns the text into a list of tokens. Each
> language has a *profile*: its keywords, operators, comment markers, and the
> way it writes strings and numbers. From the profile we build **one master
> regular expression**, with one named group per kind of token: comments,
> strings, numbers, names, symbols, and a last group `.` that matches any other
> character. Starting at the first character, we ask which group matches, save a
> token with its line and column, and continue right after it, so it is a single
> left-to-right pass. A name becomes a keyword if it is in the profile's keyword
> set, otherwise an identifier. Every token lands in one of 8 categories, and
> those counts are the totals in the report: Example 1 gives exactly 14.

**Three rules make it reliable:**
- **Order matters:** comments and strings are tried before operators, and longer
  operators before shorter ones (`**=` before `**` before `*`), so `//` is a
  comment and not two slashes.
- **It never stops:** the last group `.` matches anything, so an illegal
  character becomes an *invalid* token and lexing continues.
- **Positions:** every token keeps its line and column, so errors point to the
  exact place.

**Show:** [`tokenize()`](../syntaxlens/lexer.py#L83) (the loop) and
[`_master_pattern()`](../syntaxlens/lexer.py#L144) (how the regex is built).
In the web app, the **Tokens** tab lists every token with its category.

**Follow-ups:**
- *Why a regex and not Python's `ast` module?* `ast` only reads Python and stops
  at the first error. Example 2 needs all three errors, and we also read Java, C,
  C++ and C#.
- *How do you know the tokenizer is right?* A test compares our Python tokens
  with Python's own `tokenize` module, token by token
  ([`test_lexer_vs_cpython.py`](../tests/test_lexer_vs_cpython.py)).

### Q2. "What data structure did you use to verify balanced delimiters, and how does it handle nested brackets?"

**Who:** Ariz

**Say:**
> A **stack**. Reading the statement from left to right, every opening bracket
> `(`, `[` or `{` is pushed with its line and column. A closing bracket must match
> the bracket on **top** of the stack, which is the most recently opened one. If
> it matches, we pop it. That is what makes nesting work: in `f(a[0])` the `]`
> closes the `[` before the `)` closes the `(`. If the top does not match, it is
> a mismatch; if the stack is empty, the closing bracket is unexpected. Anything
> still on the stack at the end of the statement was never closed.

**Error codes:** E101 unclosed, E102 unexpected closing bracket, E103 mismatched.

**Two details:**
- Brackets inside strings and comments are never seen, because the lexer already
  made each string or comment a single token.
- In Java, C, C++ and C#, block braces `{ }` are matched across the whole file
  with a second stack of open blocks; `( )` and `[ ]` must close inside their
  own statement.

**Show:** [`scan()`](../syntaxlens/checks/delimiters.py#L41) (the stack) and
[`_check_blocks()`](../syntaxlens/checks/delimiters.py#L94) (block braces).

**Try:** `x = (a[0] + (b * 2))` → PASSED. `x = (a[0)]` → `[` unclosed before `)`.
`if (x > 5` → E101.

**Follow-up:** *Why not just count brackets?* A counter says `( ]` and `([)]` are
balanced. Only a stack checks the **order** and the **kind** of bracket.

### Q3. "How does your algorithm distinguish between an operator used correctly (e.g. `+5`) and an operator error (e.g. `+ *`)?"

**Who:** Gabriel

**Say:**
> The operator check is a machine with **two states**: *expecting a value* or
> *expecting an operator*. It starts by expecting a value. A name, number or
> string switches it to *expecting an operator*; a binary operator such as `+`
> switches it back. Now the key part: if a `+` or `-` (or `!`, `not`) arrives
> while we are **expecting a value**, it is a **sign**, which is allowed, and we
> keep expecting the value. So `x = +5` is fine. In `20 + * 5`, after `+` we
> expect a value, but `*` comes, and `*` cannot be a sign, so it is error E401:
> two operators with no value between them.

**The other errors from the same machine:**

| Input | What happens | Code |
|---|---|---|
| `y = 20 + * 5` | operator while expecting a value | E401 |
| `x = 5 +` | the expression ends while still expecting a value | E402 |
| `x = 5 6` | a value while expecting an operator | E403 |
| `5 = x` | the left side of `=` is not a variable | E404 |

**Five languages, one engine:** the shared code never asks "is this Java?". Each
language switches on rules in [`profiles/rules.py`](../syntaxlens/profiles/rules.py).
For example C and C++ turn on `pointer_operators`, so `*p` and `&x` are accepted
before a name, while `20 + * 5` is still an error because a number follows the `*`.
A test fails if anyone writes a language name check in the shared code
([`test_shared_code_does_not_branch_on_language_names`](../tests/test_language_rules.py#L220)).

**Show:** the explanation at the top of [`expressions.py`](../syntaxlens/expressions.py#L1)
and the loop in [`expression()`](../syntaxlens/expressions.py#L87).

**Follow-up:** *Is `x + 1;` an error?* In Java and C# yes ("not a statement",
E406). In C and C++ it is legal, so it is only a warning (W406). That is the
`discarded_value` rule.

### Q4. "How does your program handle line breaks, tabs, and comments when analyzing uploaded files?"

**Who:** Brix

**Say:**
> **Line breaks:** first the file's bytes are decoded, then every Windows `\r\n`
> and old Mac `\r` is changed to `\n`, so a file gives the same line numbers on
> any computer. A statement can continue on the next line (an open bracket, or a
> backslash in Python); the statement builder joins those lines.
>
> **Tabs:** spaces and tabs between tokens are skipped. For Python indentation,
> a tab moves to the next multiple of 8, exactly like Python itself. We also
> measure with a tab counting as 1; if the two results disagree, tabs and spaces
> were mixed, and we report E704.
>
> **Comments:** the regex reads a whole comment (`#`, `//`, `/* */`) as one token.
> It is counted in the *Comments* category and then removed before statements
> are built, so a bracket or quote inside a comment is never checked. An unclosed
> `/*` is error E803.

**Show:** [`_normalize_newlines()`](../syntaxlens/source.py#L162),
[`_width()`](../syntaxlens/structure.py#L454) (tab width),
[`_code_tokens()`](../syntaxlens/structure.py#L285) (comments removed).

**Try:** analyze `# comment with ( [ {` followed by `x = 1` → no bracket errors.

### Q5. "What error handling is in place if a user uploads a blank file or a non-text file?"

**Who:** Brix

**Say:**
> Every input goes through [`source.py`](../syntaxlens/source.py) before analysis:
> - **Too large:** files over 2 MB are refused (on the command line, even before
>   the file is read).
> - **Not text:** a NUL byte, or more than 10% invisible control characters,
>   means a binary file such as an image. We refuse it with "looks like a binary
>   file (for example an image or a compiled program), not source code."
> - **Encoding:** a byte-order mark, UTF-8, Windows-1252 (Notepad's "ANSI") and
>   Latin-1 are tried in that order, so an odd encoding never crashes the program.
> - **Blank:** an empty or whitespace-only file gives "is empty: there is no code
>   to analyze."
>
> Nothing crashes: the command line prints the message and exits with code 2, and
> the web app shows it in a red box.

**Show:** [`from_bytes()`](../syntaxlens/source.py#L101),
[`_decode()`](../syntaxlens/source.py#L127),
[`_mostly_control_characters()`](../syntaxlens/source.py#L154),
and the blank check in [`web/app.py`](../syntaxlens/web/app.py#L120).

**Try:** upload `docs/images/web-app.png`, then `empty.txt`.

### Q6. "How do you prevent string literal contents (e.g. `"if (x > 0)"`) from being parsed as actual code syntax?"

**Who:** Ariz

**Say:**
> The lexer reads the whole string as **one token**, before any check runs. In
> the master regex the string patterns come before operators and brackets, so at
> a `"` the string pattern matches everything up to the closing quote, including
> escaped quotes like `\"`. The checks only ever see one STRING token; they never
> look inside it. So in `print("if (x > 0)")` there is no `if` and no brackets
> for the checks to see, and it passes. If the closing quote is missing, the
> string ends at the end of the line (error E201) and the next line is analyzed
> normally. That is line 3 of Example 2.

**Per language** (from each profile): Python triple quotes and prefixes (`f""`,
`r""`), character literals `'x'` in Java and C, C++ raw strings `R"(...)"`,
C# `@"verbatim"` and `$"interpolated"`.

**Show:** [`_literal_patterns()`](../syntaxlens/lexer.py#L173).

**Try:** `print("if (x > 0)")` → PASSED. `print("hi)` → E201.
`print(“hi”)` (curly quotes pasted from Word) → E804.

### Q7. "How does your parser recover after finding an error on line 2 so it can continue checking line 3?"

**Who:** Marco

**Say:**
> Three layers:
> 1. **The lexer never stops.** An illegal character becomes an invalid token, and
>    an unclosed string ends at the end of its line.
> 2. **The statement builder re-syncs at every line break.** Inside an unfinished
>    statement it asks: does this line end with a complete value (`5`, `x`, `)`)
>    while the next line starts something new (`print(`, `int y`)? If so, the
>    statement ends here. The missing `)` or `;` is reported on **this** line,
>    and the next line starts fresh. That is why the unclosed `(` on line 2 of
>    Example 2 does not swallow line 3.
> 3. **A filter keeps only the root cause.** For example, an unclosed string hides
>    the bracket and operator errors it caused in the same statement.
>
> The result: Example 2 gives exactly its three errors, on lines 2, 3 and 4.
> Python's own parser stops after the first one.

**Show:** the explanation at the top of [`structure.py`](../syntaxlens/structure.py#L17),
[`_python_continues()`](../syntaxlens/structure.py#L346), and
[`filter_cascades()`](../syntaxlens/analyzer.py#L114).

**Follow-up:** *How do you know it reports the right line?* We measured it:
[`tools/measure_accuracy.py`](../tools/measure_accuracy.py) plants 1,601 known
mistakes, one at a time, in valid programs, and 98.3% are reported on exactly
the line where they were planted.

### Q8. "Which specific module or syntax check did you personally implement? Walk us through your source code."

**Everyone.** Answer truthfully: say what you wrote, fixed, tested or studied, and
then show that you understand it. Use the same four steps for any module:

1. **What goes in, what comes out.** ("`scan` gets one statement's tokens and
   returns the bracket errors in it.")
2. **The main function in plain words,** pointing at the lines.
3. **One example,** traced by hand through the code.
4. **One test** that proves it works.

| Member | Walk through | A test to show |
|---|---|---|
| Marco | [`tokenize()`](../syntaxlens/lexer.py#L83), then [`filter_cascades()`](../syntaxlens/analyzer.py#L114) | [`test_spec_examples.py`](../tests/test_spec_examples.py) |
| Gabriel | [`LanguageRules`](../syntaxlens/profiles/rules.py), then how [`operators.py`](../syntaxlens/checks/operators.py) picks the `discarded_value` handler | [`test_language_rules.py`](../tests/test_language_rules.py) |
| Ariz | The C, C++ and C# profiles in [`cfamily.py`](../syntaxlens/profiles/cfamily.py), then [`scan()`](../syntaxlens/checks/delimiters.py#L41) | [`test_checks_cfamily.py`](../tests/test_checks_cfamily.py) |
| Brix | [`from_bytes()`](../syntaxlens/source.py#L101) and [`_analyze()`](../syntaxlens/web/app.py#L98) | [`test_source.py`](../tests/test_source.py), [`test_web.py`](../tests/test_web.py) |

To run the tests during the defense: `py -m pip install -e ".[dev]"` once, then
`py -m pytest`.

---

## 5. Other likely questions

| Question | Short answer |
|---|---|
| Why Python? | Readable for everyone, and the standard library has everything we need: no installs. |
| Which libraries? | Only Python's standard library: `re` (regex), `dataclasses`, `enum`, `wsgiref` (web server). The editor in the page is CodeMirror. Tests use pytest. |
| How is the language detected? | [`detect.py`](../syntaxlens/detect.py): the user's choice first, then the file extension, then weighted clues in the code (`def …:` for Python, `System.out.println` for Java, `#include` for C/C++, `Console.WriteLine` for C#). |
| How does the web app work? | A small WSGI app ([`web/app.py`](../syntaxlens/web/app.py)) calls the **same** `analyze()` function as the command line, so both always agree. It runs offline with `run.bat` and online on Vercel. |
| How do you check identifiers? | A name must start with a letter or `_`, contain only letters, digits and `_`, and not be a reserved word: `2total` E601, `my-var` E602, `class = 5` E603. |
| How do you check Python indentation? | A stack of indentation levels, the same method Python uses: deeper than expected is E701 (unexpected indent), a header with no indented block is E702. |
| How do you check control headers? | A small grammar for each: `if` needs a condition and `:` (Python) or `( )` (C family); `for i range(10):` is missing `in` (E503); `for (i = 0, i < 5, i++)` has commas instead of `;`. |
| What is the error rate? | Measured: 98.3% of 1,601 planted mistakes are reported on the right line, and there are 0 false alarms on 19 valid programs. |
| How do you know it all works? | 606 automated tests run on Windows and Linux with five Python versions on every push to GitHub. Both specification examples are reproduced word for word. |
| What are its limits? | It checks **syntax, not meaning**: an undefined variable or a wrong type is not reported. It is not a full compiler grammar, so a few rare constructs are not understood: C# LINQ queries (`from x in xs select x`) and `switch` expressions, statements inside Java lambda bodies (not checked one by one), and C macros (not expanded). Our rule is: when unsure, do not flag, because a false alarm is worse than a missed error. |
| What would you improve next? | A full grammar for each language, JavaScript support, and checking statements inside lambdas. |
