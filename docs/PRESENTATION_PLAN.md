# SyntaxLens: Presentation Plan for the Four of Us

*Taglish version: [GABAY_TAGLISH.md](GABAY_TAGLISH.md)*

**Defense:** Tuesday, October 13 · about 12 minutes of presentation, then questions.
Every part below has three things: **what you say**, **what you demonstrate**, and
**what you must study**. The full answers to the panel's sample questions are in
[DEFENSE_GUIDE.md](DEFENSE_GUIDE.md); this file tells each of us what to do.

| # | Who | Part | Time |
|---|---|---|---|
| 1 | **Marco** | Opening: what SyntaxLens is and how it is built | 1 min |
| 2 | **Brix** | Live demo: the three input modes and file handling | 3½ min |
| 3 | **Marco** | Tokenizer: how code becomes tokens | 1½ min |
| 4 | **Ariz** | Brackets, strings, and the C / C++ / C# languages | 2½ min |
| 5 | **Gabriel** | Operators (`+5` vs `+ *`) and the language rules | 2½ min |
| 6 | **Marco** | Error recovery, testing, limits, closing | 1½ min |
| | **All** | Questions from the panel | rest |

**How this plan earns each part of the grading rubric**

| Rubric criterion | Weight | What earns it | Where |
|---|---|---|---|
| Functional correctness | 30% | Show **valid** code passing as well as errors, in all 3 input modes and several languages | Brix, Ariz, Gabriel |
| Technical logic | 20% | Prove nothing is hard-coded: type new code live and **invite the panel to type their own** | Marco, part 6 |
| Interface and error handling | 15% | Point at the caret, the **Fix:** line and the clear messages for bad files | Brix |
| Demonstration quality | 15% | Follow this order and the hand-overs; **show** every claim on screen instead of only saying it | Everyone |
| Oral explanation | 20% | Purpose, workflow, algorithms, choices (no syntax tree), **limitations**, and your own contribution | Everyone, see [Everyone must know](#everyone-must-know) |

**Rules for the day**

- Whoever is talking also drives the laptop. Before you start your part, press
  **Clear** and set **Language** back to **Auto-detect**.
- End your part with the hand-over sentence written in your section, so the next
  person can start right away.
- If the panel asks you about someone else's part, give the one-sentence answer
  from [Everyone must know](#everyone-must-know), then say "[Name] built that part
  and can explain it in detail."
- Speak to the panel, not to the screen. Point at the screen while you explain.

---

## Setup before we start (Brix, 10 minutes before)

1. Double-click `run.bat`. The app opens at `http://127.0.0.1:8000`. Keep the
   black console window open (minimize it).
2. Open the online app in a second browser tab as a backup:
   <https://multi-input-syntactical-analyzer-ap.vercel.app>.
3. Open VS Code on the project folder, with these tabs already open:
   `lexer.py`, `structure.py`, `analyzer.py`, `checks/delimiters.py`,
   `profiles/cfamily.py`, `expressions.py`, `profiles/rules.py`, `source.py`.
4. Open a Command Prompt in the project folder.
5. Put two files on the Desktop: `empty.txt` (an empty text file) and `hello.js`
   containing one line, `let x = 5;`.
6. Turn off sleep and notifications. Plug in the charger. Zoom the browser to 110%
   so the panel can read it.

**If something fails:** use the online tab. No internet? Use the command line.
Python broken? Show the online app on a phone.

---

## Everyone must know

The panel may ask anyone anything. Learn these by heart, even outside your part.

**What SyntaxLens is (one breath):** a web app and command-line tool that checks
Python, Java, C, C++ and C# code for syntax errors without running it. You can
give it a single line, a block of code, or a file.

**The 7 stages, one sentence each:**

1. **Source:** reads the input, fixes line endings, refuses empty, binary or huge files.
2. **Detect:** picks the language: your choice, else the file extension, else clues in the code.
3. **Lexer:** one big regular expression cuts the code into tokens in 8 categories.
4. **Statements:** groups the tokens into statements (lines in Python; `;` and `{ }` in C-style languages).
5. **8 checks:** brackets, strings, terminators, operators, control headers, names, indentation and blocks, illegal characters.
6. **Filter:** keeps the real cause of each mistake and drops the errors it caused.
7. **Report:** the spec-format report, a detailed report, JSON, and the web page.

**Numbers:** 3 input modes · 8 checks · 8 token categories · 5 languages ·
Example 1 = 14 tokens · Example 2 = 3 errors · 610 tests · 0 false alarms on 19
valid programs · 98.3% of 1,601 planted mistakes caught on the right line ·
standard library only.

**Why we did not build a syntax tree** (the rubric mentions "tree construction"):
> A parser that builds a full syntax tree stops at the first error. The spec's
> Example 2 needs all three errors, so we use a token list, statements, a bracket
> stack and an operator state machine instead. They can report an error and keep
> checking the next line.

**Implementation choices:** Python with only the standard library (every part is
our own code); one `analyze()` function shared by the web app and the command
line; each language is data (a profile and its rules), not separate code.

**Limitations (say them yourselves; the rubric asks for them):**
- It checks **syntax, not meaning**: an undefined variable or a wrong type is not reported.
- A few rare constructs are not understood: C# LINQ queries and `switch`
  expressions; statements inside Java lambda bodies are not checked one by one;
  C macros are not expanded.
- JavaScript and other languages are not supported (a `.js` file gets a clear message).

**Q8 ("What did you personally do? Walk us through your code"):** tell the truth
about what you wrote, fixed, tested or studied. Then walk through your file in four
steps: (1) what goes in and what comes out, (2) the main function in plain words,
(3) one example traced by hand, (4) one test that proves it.

---

## 1 and 3 and 6. Marco: opening, tokenizer, recovery, closing

**Your questions:** Q1 (tokenizing) and Q7 (recovery).
Full answers: [DEFENSE_GUIDE.md, Q1](DEFENSE_GUIDE.md#q1-how-does-your-application-tokenize-input-text-before-checking-for-syntax-errors)
and [Q7](DEFENSE_GUIDE.md#q7-how-does-your-parser-recover-after-finding-an-error-on-line-2-so-it-can-continue-checking-line-3).

### Part 1: Opening (1 min)

**Say:**
> Good morning. We are Marco, Gabriel, Ariz and Brix, and this is **SyntaxLens**,
> our Multi-Input Syntactical Analyzer. It checks code for syntax errors **without
> running it**, in five languages: Python, Java, C, C++ and C#. You can give it
> one line, a block, or a file, through a web app or the command line.
> Inside, it is a pipeline of seven small stages: read the input, detect the
> language, cut the code into tokens, group them into statements, run eight
> checks, keep only the real causes, and print the report. We wrote it in Python
> using only the standard library, so every part is our own code.
> Brix will first show you the app.

**Demonstrate:** nothing yet. If there is a projector, show the README diagram or
the User Manual's architecture table for a few seconds.

### Part 3: The tokenizer (1½ min)

**Say:**
> Every check works on tokens, so this comes first. Each language has a profile:
> its keywords, operators, comment markers, and how it writes strings and numbers.
> From that we build **one regular expression** with a named part for each kind
> of token. We start at the first character, see which part matches, save the
> token with its line and column, and continue after it. Comments and strings are
> tried first, and the longest operators first, so `**=` is never cut into
> pieces. The last part matches any single character, so an illegal character
> becomes an "invalid" token and the lexer never stops.

**Demonstrate:**

1. In the Command Prompt:
   ```bat
   py -m syntaxlens tokens samples\spec_example_1.py
   ```
   → 14 numbered tokens with line:column and category, then the summary:
   *Total Tokens Parsed: 14*, the same number as the specification.
2. In the web app: **Code Block** → *Load a sample* → **Spec Example 1** →
   **Analyze** → open the **Tokens** tab and click a category filter (for example
   *Operators*).
3. In VS Code, open `lexer.py`:
   - [`_master_pattern()`](../syntaxlens/lexer.py#L144): point at the list of
     named parts, the line that sorts operators longest-first, and the final `"."`.
   - [`tokenize()`](../syntaxlens/lexer.py#L83): point at the `while` loop: match,
     save the token, move on.

**Hand over:** "Now Ariz will show how we use these tokens to check brackets and strings."

### Part 6: Recovery, testing and closing (1½ min)

**Say:**
> A normal compiler stops at the first error. Ours keeps going, in three ways.
> The lexer never stops. At every line break inside an unfinished statement, the
> statement builder asks: does this line end with a complete value while the next
> line starts something new? If so, the missing `)` or `;` is reported on this
> line and the next line starts fresh. Finally, a filter keeps only the root
> cause, so one mistake is not reported three times. That is why Example 2 gives
> exactly its three errors. Python itself reports only the first one.

**Demonstrate:**

1. **Code Block** → *Load a sample* → **Python - one error of each kind** →
   **Analyze** → 9 errors on 9 different lines; open **Line Breakdown** and scroll:
   each line says OK or which error it has. The broken line 3 did not stop lines 4–13.
2. In VS Code, open the explanation at the top of
   [`structure.py`](../syntaxlens/structure.py#L17) ("Recovering from mistakes"),
   then [`filter_cascades()`](../syntaxlens/analyzer.py#L114).
3. **Panel challenge** (this proves nothing is hard-coded, rubric criterion 2). Go to
   **Single Line**, set Language to **Auto-detect**, and say:
   > "Everything so far was prepared. Please give us any line of code, correct or
   > wrong, and we will analyze it now."

   Type exactly what they say and press Enter. If they decline, type this yourself:
   - Python, `x = 3; y = 6; print(x + y);` → **PASSED**. Say: "This looks wrong,
     but Python allows `;` between statements, and real Python runs it and prints 9.
     Flagging it would be a false alarm."
   - Then set Language to **Java** and type `int total = x + y` → **missing
     semicolon** (E301). Say: "In Java the same `;` is required."

**Closing, say:**
> To make sure it works, we have 610 automated tests that run on Windows and Linux
> on every change, including both examples from the specification. We also
> planted 1,601 known mistakes into correct programs, and 98.3% were reported on
> the exact line. Its limits: it checks syntax, not meaning, so it does not know
> whether a variable exists; a few rare constructs like C# LINQ queries are not
> supported; and we did not build a full syntax tree, on purpose, because a tree
> parser stops at the first error. Thank you. We are ready for your questions.

### Marco: study checklist

- [ ] Explain the 7 stages without notes.
- [ ] Explain the master regex: named groups, order (comments and strings first,
      longest operators first), the final `.`, line and column.
- [ ] Explain why Example 1 has exactly 14 tokens (count them on the token list).
- [ ] Explain the three layers of recovery, using Example 2 line by line.
- [ ] Answer: *Why not Python's `ast` module?* It reads only Python and stops at
      the first error; Example 2 needs all three errors.
- [ ] Answer: *How do you know the tokenizer is right?* A test compares our Python
      tokens with Python's own `tokenize` module
      ([`test_lexer_vs_cpython.py`](../tests/test_lexer_vs_cpython.py)).
- [ ] Q8 walk-through: [`tokenize()`](../syntaxlens/lexer.py#L83), test:
      [`test_spec_examples.py`](../tests/test_spec_examples.py).

---

## 2. Brix: the three input modes and file handling (3½ min)

**Your questions:** Q4 (line breaks, tabs, comments) and Q5 (blank or non-text files).
Full answers: [DEFENSE_GUIDE.md, Q4](DEFENSE_GUIDE.md#q4-how-does-your-program-handle-line-breaks-tabs-and-comments-when-analyzing-uploaded-files)
and [Q5](DEFENSE_GUIDE.md#q5-what-error-handling-is-in-place-if-a-user-uploads-a-blank-file-or-a-non-text-file).

**Say (start):**
> The specification asks for three input modes, and SyntaxLens has all three, both
> in this web app and on the command line. I will show each one.

**Demonstrate, and say one sentence before each step:**

1. **Mode 1, Single Line.** Click the chip **`y = 20 + * 5`**, press **Enter**.
   → *FAILED*, error E401: "Consecutive binary operators '+ *'". Point at the red
   wavy line under `*`, the caret in the error card, and the green **Fix** line.
   Then click **`System.out.println("Hello");`** → *PASSED*, Java detected
   automatically. Then **`System.out.println("Hello")`** → missing semicolon.
2. **Mode 2, Code Block.** *Load a sample* → **Spec Example 2 - three errors** →
   **Analyze**.
   → exactly the specification's three errors, marked in the code with red lines
   and dots. Point at the counters and the two bar charts.
   Open the **Report** tab → **Classic (spec format)**:
   > "This is the specification's report format, line for line. The only line we
   > changed on purpose is *Target Syntax Rule*: it names the language we detected."
   Click **Detailed** to show the codes, carets and fixes. Mention **Copy** and
   **Download .txt / .json**.
3. **Mode 3, Upload File.** Click the **Upload File** tab and drag
   `samples\ErrorsDemo.java` from File Explorer onto the box.
   → 10 errors. Click an error card: the editor jumps to that line.
   Then upload `samples\HelloWorld.java` → **PASSED**. Say: "A correct file passes,
   so it is not just finding errors everywhere."
4. **Bad files** (this is Q5, so say it clearly):
   - Upload `docs\images\web-app.png` → "looks like a binary file ... not source code".
   - Upload `empty.txt` from the Desktop → "is empty: there is no code to analyze".
   - Upload `hello.js` from the Desktop → "JavaScript (.js) is not supported ...".
   > "Nothing crashes. Before analysis, every file is checked: over 2 MB is refused,
   > a file containing a NUL byte or mostly invisible control characters is binary, and
   > an empty file has nothing to analyze."
5. **Command line** (if time allows), in the Command Prompt:
   ```bat
   py -m syntaxlens line "y = 20 + * 5"
   py -m syntaxlens file samples\spec_example_2.py --style classic
   ```
   > "Same engine, same results. The web app and the command line call the same
   > `analyze()` function."

**Hand over:** "Marco will now explain what happens inside when we press Analyze."

**Open in the code (if asked, or for Q8):**

- [`source.py`](../syntaxlens/source.py): [`from_bytes()`](../syntaxlens/source.py#L101)
  (size limit), [`_decode()`](../syntaxlens/source.py#L127) (byte-order mark, NUL
  byte, UTF-8, Windows-1252, Latin-1),
  [`_mostly_control_characters()`](../syntaxlens/source.py#L154) (more than 10% → binary),
  [`_normalize_newlines()`](../syntaxlens/source.py#L162) (`\r\n` and `\r` → `\n`).
- [`web/app.py`](../syntaxlens/web/app.py): [`_analyze()`](../syntaxlens/web/app.py#L98):
  a file arrives as base64 bytes and goes through the same `from_bytes()` as the
  command line.

### Brix: study checklist

- [ ] Do the whole demo twice on the presentation laptop, with a timer (under 3½ min).
- [ ] Explain each of the four refusals: too big, binary, empty, unsupported
      language (a `.js` file says "JavaScript is not supported").
- [ ] Explain line breaks: Windows `\r\n` and old Mac `\r` become `\n`, so line
      numbers are the same on every computer.
- [ ] Explain tabs: for Python indentation a tab moves to the next multiple of 8,
      like Python; mixing tabs and spaces is error E704.
- [ ] Explain comments: a comment is one token, counted under *Comments*, then
      removed before checking, so `# ( [ {` causes no bracket error.
      Try it: Single Line, `x = 1 # comment (` → PASSED.
- [ ] Know the report parts: status, counts, line breakdown, error details, totals
      per category (the specification asks for both lists and totals).
- [ ] Q8 walk-through: [`from_bytes()`](../syntaxlens/source.py#L101) and
      [`_analyze()`](../syntaxlens/web/app.py#L98); tests:
      [`test_source.py`](../tests/test_source.py), [`test_web.py`](../tests/test_web.py).

---

## 4. Ariz: brackets, strings, and C / C++ / C# (2½ min)

**Your questions:** Q2 (bracket stack) and Q6 (strings are not parsed).
Full answers: [DEFENSE_GUIDE.md, Q2](DEFENSE_GUIDE.md#q2-what-data-structure-did-you-use-to-verify-balanced-delimiters-and-how-does-it-handle-nested-brackets)
and [Q6](DEFENSE_GUIDE.md#q6-how-do-you-prevent-string-literal-contents-eg-if-x--0-from-being-parsed-as-actual-code-syntax).

**Say:**
> For brackets we use a **stack**. Every opening bracket is pushed. A closing
> bracket must match the one on top, which is the most recently opened one, and
> then we pop it. That is how nesting works: the inner bracket must close first.
> If the closing bracket does not match, or nothing is open, it is an error. If
> something is still on the stack at the end, it was never closed.
>
> Brackets inside strings are never checked, because the lexer already turned the
> whole string into **one token** before any check runs.

**Demonstrate (Single Line, Language: Auto-detect):**

| Type this | Result | Say |
|---|---|---|
| `x = (a[0] + (b * 2))` | PASSED | "Three levels of nesting, all closed in the right order." |
| `x = (a[0)]` | 2 errors | "The `)` arrives while `[` is on top: the `[` was never closed, and the last `]` has nothing to close." |
| `if (x > 5` | E101 | "Left on the stack at the end of the line." |
| `print("if (x > 0)")` | PASSED | "The `if` and the brackets are inside one string token, so no check sees them." |
| `name = "SyntaxLens` | E201 | "No closing quote: the string stops at the end of the line, and the next line is checked normally." |

Then show the C family: **Code Block** → *Load a sample* → **C++ - common mistakes**
→ **Analyze** → C++ detected automatically, 10 errors and 1 warning. Point at
line 9, `char grade = 'AB';` → E204: a character literal must hold one character.

**Open in the code:**

- [`scan()`](../syntaxlens/checks/delimiters.py#L41): the `stack` list, the
  `append` (push), the comparison with `stack[-1]` (the top), the `pop`, and the
  loop at the end that reports what is left.
- [`_check_blocks()`](../syntaxlens/checks/delimiters.py#L94): in Java, C, C++ and
  C#, `{ }` blocks are matched across the whole file.
- [`_literal_patterns()`](../syntaxlens/lexer.py#L173): the complete string pattern,
  then the `_OPEN` pattern that stops at the end of the line.
- [`profiles/cfamily.py`](../syntaxlens/profiles/cfamily.py): the C, C++ and C#
  profiles: keywords, operators, quotes (C++ raw strings `R"(...)"`,
  C# `@"..."` and `$"..."`).

**Hand over:** "Gabriel will show how we check operators, and how one engine handles five languages."

### Ariz: study checklist

- [ ] Draw the stack on paper for `f(a[0])` and for `x = (a[0)]`, step by step.
- [ ] Answer: *Why not just count brackets?* A counter thinks `([)]` is fine. A
      stack checks the order and the kind.
- [ ] Know the codes: E101 unclosed, E102 unexpected closing, E103 mismatched,
      E201 unclosed string, E204 bad character literal.
- [ ] Explain why a string is one token: string patterns come before brackets and
      operators in the master regex.
- [ ] Explain how the language is detected (`detect.py`): your choice, else the
      extension, else clues such as `#include <iostream>` for C++ and
      `Console.WriteLine` for C#.
- [ ] Q8 walk-through: the profiles in [`cfamily.py`](../syntaxlens/profiles/cfamily.py),
      then [`scan()`](../syntaxlens/checks/delimiters.py#L41); test:
      [`test_checks_cfamily.py`](../tests/test_checks_cfamily.py).

---

## 5. Gabriel: operators and the language rules (2½ min)

**Your question:** Q3 (`+5` versus `+ *`).
Full answer: [DEFENSE_GUIDE.md, Q3](DEFENSE_GUIDE.md#q3-how-does-your-algorithm-distinguish-between-an-operator-used-correctly-eg-5-and-an-operator-error-eg--).

**Say:**
> The operator check is a machine with **two states**: expecting a value, or
> expecting an operator. A name or number moves it to "expecting an operator". A
> binary operator like `+` moves it back to "expecting a value". If a `+` or `-`
> comes while we are expecting a value, it is a **sign**, which is fine, so `+5`
> passes. But in `20 + * 5`, after the `+` we expect a value and get `*`, which
> cannot be a sign: that is the error.

**Demonstrate, part 1 (Single Line, Language: Auto-detect):**

| Type this | Result | Say |
|---|---|---|
| `x = +5` | PASSED | "`+` while expecting a value: a sign." |
| `x = -(-5)` | PASSED | "Signs and brackets nest too." |
| `y = 20 + * 5` | E401 | "An operator while expecting a value." |
| `x = 5 +` | E402 | "The line ends while we still expect a value." |
| `x = 5 6` | E403 | "A value while expecting an operator." |
| `5 = x` | E404 | "You cannot assign to a number." |

**Say:**
> We support five languages without writing "if Java, then ..." in the checks.
> Each language switches rules on or off in one table, `LanguageRules`. Two examples:

**Demonstrate, part 2 (change the Language menu):**

| Language | Type this | Result | Say |
|---|---|---|---|
| C | `int *p = &x;` | PASSED | "C has pointers: `*` and `&` before a name are allowed (`pointer_operators`)." |
| C | `int y = 20 + * 5;` | E401 | "But `* 5` is still an error: a pointer needs a name, not a number." |
| Java | `x + 1;` | E406 error | "Java rejects a value that is computed and thrown away." |
| C | `x + 1;` | W406 warning | "C allows it, so it is only a warning (`discarded_value`)." |

**Open in the code:**

- The explanation at the top of [`expressions.py`](../syntaxlens/expressions.py#L1)
  (the two states), then [`expression()`](../syntaxlens/expressions.py#L87): the
  `state == EXPECT_OPERAND` branch, the sign check (`self.prefix`), and the E401 report.
- [`profiles/rules.py`](../syntaxlens/profiles/rules.py): the `LanguageRules`
  table, and where C turns on `pointer_operators` in
  [`cfamily.py`](../syntaxlens/profiles/cfamily.py).
- The guard test [`test_shared_code_does_not_branch_on_language_names`](../tests/test_language_rules.py#L220):
  it fails if anyone writes a language-name check in the shared code.

**Hand over:** "Marco will finish with how the analyzer keeps going after an error."

### Gabriel: study checklist

- [ ] Trace `y = 20 + * 5` on paper token by token, writing the state after each one.
- [ ] Trace `x = +5` the same way and point at where the sign is accepted.
- [ ] Know the codes: E401 two operators, E402 missing value after, E403 missing
      operator, E404 bad assignment target, E406 / W406 discarded value.
- [ ] Explain three rules from `rules.py` in one sentence each (for example
      `pointer_operators`, `discarded_value`, `type_body_semicolon`).
- [ ] Explain how the right handler is chosen for `x + 1;`: the `_DISCARDED_VALUE`
      table in [`operators.py`](../syntaxlens/checks/operators.py), keyed by the rule.
- [ ] Q8 walk-through: [`LanguageRules`](../syntaxlens/profiles/rules.py) and the
      `_DISCARDED_VALUE` table; test: [`test_language_rules.py`](../tests/test_language_rules.py).

---

## Practice plan for October 12

1. **Run-through 1 (30 min):** everyone in their order, with a timer. Write down
   what took too long.
2. **Swap quiz (20 min):** each person asks another member two questions from
   [DEFENSE_GUIDE.md](DEFENSE_GUIDE.md) sections 4 and 5. Answer without the page.
3. **Run-through 2 (15 min):** on the presentation laptop, using `run.bat`.
4. **Q8 practice (5 min each):** walk through your file out loud to the others.
