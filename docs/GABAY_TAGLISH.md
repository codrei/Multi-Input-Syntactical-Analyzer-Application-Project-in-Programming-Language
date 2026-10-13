# SyntaxLens: Gabay sa Presentation (Taglish)

Ito yung Taglish version ng [PRESENTATION_PLAN.md](PRESENTATION_PLAN.md). Pareho lang
ang laman, mas madali lang basahin.

- Yung mga explanation, steps at checklist: **Taglish**.
- Yung mga linya na may **"Sabihin"**: **English**, kasi English ang presentation.
  Sa ilalim ng bawat isa may **"Ibig sabihin"** na Taglish, para gets niyo talaga
  yung sinasabi niyo. Okay lang kung hindi word-for-word, basta tama yung idea.

**Presentation:** Tuesday, October 13 · mga 12 minutes, tapos Q&A.

| # | Sino | Parte | Oras |
|---|---|---|---|
| 1 | **Marco** | Opening: ano ang SyntaxLens at paano siya ginawa | 1 min |
| 2 | **Brix** | Live demo: yung 3 input modes at mga sirang file | 3½ min |
| 3 | **Marco** | Tokenizer: paano nagiging tokens ang code | 1½ min |
| 4 | **Ariz** | Brackets, strings, at C / C++ / C# | 2½ min |
| 5 | **Gabriel** | Operators (`+5` vs `+ *`) at language rules | 2½ min |
| 6 | **Marco** | Error recovery, testing, limitations, closing | 1½ min |
| | **Lahat** | Q&A ng panel | natitirang oras |

---

## Paano natin makukuha yung bawat parte ng rubric

| Rubric | Bigat | Ano ang gagawin natin | Sino |
|---|---|---|---|
| Functional correctness | 30% | Ipakita na **pumapasa yung tamang code**, hindi lang errors. Lahat ng 3 input modes, iba't ibang languages. | Brix, Ariz, Gabriel |
| Technical logic | 20% | Patunayan na walang naka-hard-code: mag-type ng bagong code live, at **paanyayahan ang panel na mag-type ng sarili nila**. | Marco, part 6 |
| Interface at error handling | 15% | Ituro yung caret (`^`), yung **Fix:** na linya, at yung malinaw na message sa sirang file. | Brix |
| Demonstration quality | 15% | Sundin yung order at hand-over. **Ipakita** sa screen yung bawat sinasabi, huwag lang i-describe. | Lahat |
| Oral explanation | 20% | Purpose, workflow, algorithms, bakit ganito ang ginawa (walang syntax tree), **limitations**, at contribution niyo. | Lahat |

---

## Rules sa mismong araw

- Kung sino ang nagsasalita, siya rin ang hahawak ng laptop. Bago ka magsimula,
  pindutin ang **Clear** at ibalik ang **Language** sa **Auto-detect**.
- Tapusin ang parte mo gamit yung **hand-over** na linya, para tuloy-tuloy.
- Kung tinanong ka tungkol sa parte ng iba: sagutin mo gamit yung one-sentence
  answer sa [Dapat alam ng lahat](#dapat-alam-ng-lahat), tapos sabihin mo:
  "[Pangalan] built that part and can explain it in detail."
- Sa panel ka tumingin, hindi sa screen. Ituro mo lang yung screen habang
  nag-e-explain.

---

## Setup bago magsimula (Brix, 10 minutes before)

1. I-double-click ang `run.bat`. Magbubukas yung app sa `http://127.0.0.1:8000`.
   **Huwag isara** yung itim na console window (i-minimize lang).
2. Buksan yung online app sa pangalawang tab, backup:
   <https://multi-input-syntactical-analyzer-ap.vercel.app>
3. Buksan ang VS Code sa project folder, nakabukas na itong mga tabs:
   `lexer.py`, `structure.py`, `analyzer.py`, `checks/delimiters.py`,
   `profiles/cfamily.py`, `expressions.py`, `profiles/rules.py`, `source.py`.
4. Magbukas ng Command Prompt sa project folder.
5. Gumawa ng dalawang file sa Desktop:
   - `empty.txt`: walang laman
   - `hello.js`: may isang linya, `let x = 5;`
6. I-off ang sleep at notifications, naka-charge ang laptop, i-zoom ang browser
   sa 110% para mabasa ng panel.

**Kapag may sumablay:** gamitin yung online tab. Walang internet? Command line.
Sira ang Python? Ipakita yung online app sa phone.

---

## Dapat alam ng lahat

Pwedeng tanungin ng panel kahit sino tungkol sa kahit anong parte. Kabisaduhin ito.

**Ano ang SyntaxLens (isang hinga):** isang web app at command-line tool na
nagche-check ng syntax errors sa Python, Java, C, C++ at C# code **nang hindi
pinapatakbo** yung code. Pwedeng isang linya, isang block ng code, o isang file.

**Yung 7 stages, tig-iisang sentence:**

1. **Source:** binabasa yung input, inaayos yung line endings, tinatanggihan
   yung empty, binary o sobrang laking file.
2. **Detect:** pinipili yung language: kung ano pinili mo, kung wala, base sa file
   extension, kung wala pa rin, base sa itsura ng code.
3. **Lexer:** isang malaking regular expression ang naghahati sa code into tokens,
   naka-sort sa 8 categories.
4. **Statements:** pinagsasama-sama yung tokens into statements (sa Python, per
   linya; sa C-style languages, gamit ang `;` at `{ }`).
5. **8 checks:** brackets, strings, terminators (`;` at `:`), operators, control
   headers (`if`, `for`...), names, indentation at blocks, illegal characters.
6. **Filter:** iniiwan lang yung tunay na dahilan ng mali, tinatanggal yung mga
   error na epekto lang nun.
7. **Report:** yung report na kapareho ng format sa spec, detailed report, JSON,
   at yung web page.

**Mga numero:** 3 input modes · 8 checks · 8 token categories · 5 languages ·
Example 1 = 14 tokens · Example 2 = 3 errors · 610 tests · 0 false alarms sa 19
tamang programs · 98.3% ng 1,601 na sinadyang mali ang nahuli sa tamang linya ·
standard library lang ng Python ang ginamit.

**Bakit walang syntax tree** (kasi nabanggit sa rubric ang "tree construction"):
> **Sabihin:** "A parser that builds a full syntax tree stops at the first error.
> The spec's Example 2 needs all three errors, so we use a token list, statements,
> a bracket stack and an operator state machine instead. They can report an error
> and keep checking the next line."
>
> **Ibig sabihin:** Kapag gumawa ka ng buong tree, titigil siya sa unang mali.
> Kailangan ng Example 2 na makita lahat ng 3 mali, kaya iba ang ginamit natin
> para tuloy-tuloy ang pag-check.

**Bakit ganito ang ginawa (implementation choices):**
- Python, **standard library lang**: lahat ng parte, sarili nating code.
- Iisang `analyze()` function ang gamit ng web app at ng command line, kaya
  pareho lagi ang resulta.
- Bawat language ay **data** (profile + rules), hindi hiwalay na code.

**Limitations (tayo na mismo ang magsabi, hinahanap ito ng rubric):**
- **Syntax lang, hindi meaning**: hindi niya alam kung may variable na hindi
  na-declare o maling type.
- May ilang bihirang syntax na hindi niya naiintindihan: C# LINQ queries at
  `switch` expressions; yung mga statement sa loob ng Java lambda ay hindi
  isa-isang chine-check; hindi ine-expand yung C macros.
- Walang JavaScript at ibang languages (may malinaw na message kapag `.js` ang file).

**Q8: "Ano ang ginawa mo personally? I-walk through mo yung code."**
Sabihin ang totoo: ano ang sinulat mo, inayos mo, tinest mo, o pinag-aralan mo.
Tapos i-explain ang file mo sa 4 steps:
1. Ano ang pumapasok at ano ang lumalabas.
2. Yung main function, sa simpleng salita, habang tinuturo yung lines.
3. Isang example na tina-trace mo by hand.
4. Isang test na nagpapatunay na gumagana.

---

## 1, 3 at 6. Marco: opening, tokenizer, recovery, closing

**Tanong na sa'yo:** Q1 (paano mag-tokenize) at Q7 (paano tumutuloy pagkatapos ng error).

### Part 1: Opening (1 min)

> **Sabihin:** "Good morning. We are Marco, Gabriel, Ariz and Brix, and this is
> **SyntaxLens**, our Multi-Input Syntactical Analyzer. It checks code for syntax
> errors **without running it**, in five languages: Python, Java, C, C++ and C#.
> You can give it one line, a block, or a file, through a web app or the command
> line. Inside, it is a pipeline of seven small stages: read the input, detect the
> language, cut the code into tokens, group them into statements, run eight checks,
> keep only the real causes, and print the report. We wrote it in Python using only
> the standard library, so every part is our own code. Brix will first show you the app."
>
> **Ibig sabihin:** Pakilala, ano ang ginagawa ng app, at yung 7 stages na
> parang assembly line. Tapos ipapasa kay Brix.

**Ipakita:** wala pa. Kung may projector, ipakita saglit yung architecture table sa manual.

### Part 3: Tokenizer (1½ min)

> **Sabihin:** "Every check works on tokens, so this comes first. Each language has
> a profile: its keywords, operators, comment markers, and how it writes strings
> and numbers. From that we build **one regular expression** with a named part for
> each kind of token. We start at the first character, see which part matches, save
> the token with its line and column, and continue after it. Comments and strings
> are tried first, and the longest operators first, so `**=` is never cut into
> pieces. The last part matches any single character, so an illegal character
> becomes an invalid token and the lexer never stops."
>
> **Ibig sabihin:** Hinahati natin yung code into maliliit na piraso (tokens)
> gamit ang isang regex. Simula sa unang character, tinitingnan kung anong klase
> ng token ang tumutugma, sine-save, tapos tuloy sa susunod. Inuuna ang comments
> at strings, at inuuna ang mahahabang operator. Kapag may character na hindi
> kilala, "invalid token" siya, pero hindi titigil ang lexer.

**Ipakita:**
1. Sa Command Prompt:
   ```bat
   py -m syntaxlens tokens samples\spec_example_1.py
   ```
   → 14 tokens, may line:column at category, tapos *Total Tokens Parsed: 14*,
   kapareho ng spec.
2. Sa web app: **Code Block** → *Load a sample* → **Spec Example 1** → **Analyze**
   → buksan ang **Tokens** tab, i-click yung isang category filter (hal. *Operators*).
3. Sa VS Code, `lexer.py`:
   - [`_master_pattern()`](../syntaxlens/lexer.py#L144): ituro yung listahan ng
     named parts, yung line na nag-so-sort ng operators (pinakamahaba muna), at
     yung huling `"."`.
   - [`tokenize()`](../syntaxlens/lexer.py#L83): ituro yung `while` loop: match,
     save ng token, tuloy.

**Hand over:** "Now Ariz will show how we use these tokens to check brackets and strings."

### Part 6: Recovery, testing, closing (1½ min)

> **Sabihin:** "A normal compiler stops at the first error. Ours keeps going, in
> three ways. The lexer never stops. At every line break inside an unfinished
> statement, the statement builder asks: does this line end with a complete value
> while the next line starts something new? If so, the missing `)` or `;` is
> reported on this line and the next line starts fresh. Finally, a filter keeps only
> the root cause, so one mistake is not reported three times. That is why Example 2
> gives exactly its three errors. Python itself reports only the first one."
>
> **Ibig sabihin:** Tatlong paraan para hindi tumigil sa unang mali:
> (1) hindi tumitigil ang lexer;
> (2) sa bawat bagong linya, tinitingnan kung tapos na yung linya at may bagong
> nagsisimula, kung oo, doon ire-report yung kulang na `)` o `;` at fresh start
> yung susunod na linya;
> (3) yung filter, isang beses lang ire-report ang isang mali.
> Kaya eksaktong 3 errors ang Example 2, samantalang yung Python mismo, isa lang.

**Ipakita:**
1. **Code Block** → *Load a sample* → **Python - one error of each kind** →
   **Analyze** → 9 errors sa 9 na magkakaibang linya. Buksan ang **Line Breakdown**:
   bawat linya may OK o kung anong error. Hindi napatigil ng sirang line 3 yung
   lines 4 hanggang 13.
2. Sa VS Code: yung explanation sa taas ng [`structure.py`](../syntaxlens/structure.py#L17)
   ("Recovering from mistakes"), tapos [`filter_cascades()`](../syntaxlens/analyzer.py#L114).
3. **Panel challenge** (patunay na walang hard-coded, rubric #2). Pumunta sa
   **Single Line**, **Auto-detect**, tapos:
   > **Sabihin:** "Everything so far was prepared. Please give us any line of code,
   > correct or wrong, and we will analyze it now."
   >
   > **Ibig sabihin:** Inihanda namin lahat ng nakita niyo. Kayo naman, magbigay
   > kayo ng kahit anong code, ia-analyze namin ngayon din.

   I-type yung binigay nila, Enter. Kung ayaw nila, ikaw ang mag-type:
   - Python, `x = 3; y = 6; print(x + y);` → **PASSED**.
     > **Sabihin:** "This looks wrong, but Python allows `;` between statements, and
     > real Python runs it and prints 9. Flagging it would be a false alarm."
     >
     > **Ibig sabihin:** Mukhang mali, pero tama sa Python. Kapag ni-flag namin,
     > false alarm yun.
   - Tapos gawing **Java** ang Language at i-type `int total = x + y` →
     **missing semicolon** (E301). "In Java the same `;` is required."

> **Sabihin (closing):** "To make sure it works, we have 610 automated tests that run
> on Windows and Linux on every change, including both examples from the
> specification. We also planted 1,601 known mistakes into correct programs, and 98.3%
> were reported on the exact line. Its limits: it checks syntax, not meaning, so it
> does not know whether a variable exists; a few rare constructs like C# LINQ queries
> are not supported; and we did not build a full syntax tree, on purpose, because a
> tree parser stops at the first error. Thank you. We are ready for your questions."
>
> **Ibig sabihin:** Paano natin alam na gumagana (610 tests, 98.3%), ano ang
> limitations, salamat, handa na sa tanong.

### Marco: kung tanungin ka

- **Q1: Paano mag-tokenize?** Isang regex na binuo mula sa profile ng language.
  Simula sa unang character, hanapin kung anong token, i-save kasama ang line at
  column, tuloy. Keyword ba o identifier? Tinitingnan kung nasa listahan ng
  keywords ng language.
- **Q7: Paano tumutuloy pagkatapos ng error sa line 2?** Yung tatlong paraan sa
  Part 6: hindi tumitigil ang lexer, nire-reset sa bawat bagong linya, at may filter.
- **Bakit hindi ginamit ang `ast` module ng Python?** Python lang ang kaya niya at
  tumitigil siya sa unang error. Kailangan natin ng 3 errors sa Example 2 at
  limang languages.
- **Paano niyo nalaman na tama ang tokenizer?** May test na kinukumpara ang tokens
  natin sa sariling `tokenize` module ng Python, token per token.

### Marco: checklist

- [ ] Kaya i-explain yung 7 stages nang walang notes.
- [ ] Kaya i-explain ang master regex: named groups, yung order (comments at
      strings muna, mahabang operator muna), yung huling `.`, line at column.
- [ ] Kaya bilangin kung bakit 14 tokens ang Example 1 (tingnan yung token list).
- [ ] Kaya i-explain yung 3 paraan ng recovery gamit ang Example 2, line by line.
- [ ] Q8: [`tokenize()`](../syntaxlens/lexer.py#L83), test:
      [`test_spec_examples.py`](../tests/test_spec_examples.py).

---

## 2. Brix: 3 input modes at mga sirang file (3½ min)

**Tanong na sa'yo:** Q4 (line breaks, tabs, comments) at Q5 (blank o hindi text na file).

> **Sabihin (simula):** "The specification asks for three input modes, and SyntaxLens
> has all three, both in this web app and on the command line. I will show each one."
>
> **Ibig sabihin:** Tatlong paraan ng pag-input ang hinihingi ng spec, meron tayong
> lahat, sa web at sa command line.

**Ipakita (magsabi ng isang sentence bago ang bawat step):**

1. **Mode 1, Single Line.** I-click yung chip na **`y = 20 + * 5`**, Enter.
   → *FAILED*, E401. Ituro yung pulang wavy line sa ilalim ng `*`, yung `^` sa
   error card, at yung berdeng **Fix:** na linya.
   Tapos i-click **`System.out.println("Hello");`** → *PASSED*, kusa niyang nakitang
   Java. Tapos **`System.out.println("Hello")`** → kulang ng semicolon.
2. **Mode 2, Code Block.** *Load a sample* → **Spec Example 2 - three errors** →
   **Analyze** → eksaktong 3 errors ng spec, may pulang linya at tuldok sa code.
   Ituro yung counters at yung 2 bar charts.
   Buksan ang **Report** tab → **Classic (spec format)**:
   > **Sabihin:** "This is the specification's report format, line for line. The only
   > line we changed on purpose is *Target Syntax Rule*: it names the language we detected."
   >
   > **Ibig sabihin:** Pareho sa format ng spec. Isang linya lang ang sinadya
   > nating baguhin: sinasabi niya kung anong language ang na-detect.

   I-click ang **Detailed** para makita yung codes, `^` at fixes. Banggitin ang
   **Copy** at **Download .txt / .json**.
3. **Mode 3, Upload File.** **Upload File** tab, i-drag ang `samples\ErrorsDemo.java`
   mula sa File Explorer → 10 errors. I-click ang isang error card: tatalon ang
   editor sa linyang yun.
   Tapos i-upload ang `samples\HelloWorld.java` → **PASSED**.
   > **Sabihin:** "A correct file passes, so it is not just finding errors everywhere."
4. **Sirang files** (ito yung Q5, kaya linawin):
   - `docs\images\web-app.png` → "looks like a binary file ... not source code"
   - `empty.txt` (Desktop) → "is empty: there is no code to analyze"
   - `hello.js` (Desktop) → "JavaScript (.js) is not supported ..."
   > **Sabihin:** "Nothing crashes. Before analysis, every file is checked: over 2 MB is
   > refused, a file containing a NUL byte or mostly invisible control characters is
   > binary, and an empty file has nothing to analyze."
   >
   > **Ibig sabihin:** Walang nag-crash. Bago i-analyze, chine-check muna yung
   > file: sobrang laki, binary (larawan, exe), walang laman, o ibang language.
5. **Command line** (kung may oras):
   ```bat
   py -m syntaxlens line "y = 20 + * 5"
   py -m syntaxlens file samples\spec_example_2.py --style classic
   ```
   > **Sabihin:** "Same engine, same results. The web app and the command line call the
   > same `analyze()` function."

**Hand over:** "Marco will now explain what happens inside when we press Analyze."

### Brix: kung tanungin ka

- **Q4: Line breaks?** Ginagawang `\n` lahat ng line endings (`\r\n` ng Windows,
  `\r` ng lumang Mac), kaya pareho ang line numbers kahit saang computer.
- **Q4: Tabs?** Sa Python indentation, ang tab ay tumatalon sa susunod na
  multiple ng 8, katulad ng Python mismo. Kapag pinaghalo ang tabs at spaces,
  error E704.
- **Q4: Comments?** Isang token ang buong comment, binibilang sa *Comments*, tapos
  tinatanggal bago mag-check. Kaya yung `(` o `"` sa loob ng comment, hindi
  pinapansin. Subukan: `x = 1 # comment (` → PASSED.
- **Q5: Blank o hindi text?** Apat na check sa `source.py` bago mag-analyze:
  lampas 2 MB, binary (may NUL byte o higit 10% ay invisible na characters),
  walang laman, o hindi suportadong language. Malinaw na message, walang crash.

### Brix: checklist

- [ ] Gawin yung buong demo nang 2 beses sa presentation laptop, may timer (under 3½ min).
- [ ] Kaya i-explain yung 4 na pagtanggi sa file.
- [ ] Alam yung parts ng report: status, counts, line breakdown, error details,
      totals per category.
- [ ] Q8: [`from_bytes()`](../syntaxlens/source.py#L101) at
      [`_analyze()`](../syntaxlens/web/app.py#L98); tests:
      [`test_source.py`](../tests/test_source.py), [`test_web.py`](../tests/test_web.py).

---

## 4. Ariz: brackets, strings, C / C++ / C# (2½ min)

**Tanong na sa'yo:** Q2 (bracket stack) at Q6 (bakit hindi chine-check ang laman ng string).

> **Sabihin:** "For brackets we use a **stack**. Every opening bracket is pushed. A
> closing bracket must match the one on top, which is the most recently opened one,
> and then we pop it. That is how nesting works: the inner bracket must close first.
> If the closing bracket does not match, or nothing is open, it is an error. If
> something is still on the stack at the end, it was never closed. Brackets inside
> strings are never checked, because the lexer already turned the whole string into
> **one token** before any check runs."
>
> **Ibig sabihin:** Parang patong-patong na plato ang stack. Bawat bukas na
> bracket, ipapatong. Yung pansara, dapat tumugma sa nasa pinakaibabaw (yung
> pinakahuling binuksan), tapos aalisin. Kaya yung nasa loob, dapat unang
> isara. Kapag hindi tumugma o walang nakapatong, error. Kapag may naiwan sa
> dulo, hindi naisara. Yung string naman, isang buong token na, kaya hindi na
> nakikita ng checks yung brackets sa loob nito.

**Ipakita (Single Line, Auto-detect):**

| I-type | Resulta | Sabihin |
|---|---|---|
| `x = (a[0] + (b * 2))` | PASSED | "Three levels of nesting, all closed in the right order." |
| `x = (a[0)]` | 2 errors | "The `)` arrives while `[` is on top: the `[` was never closed, and the last `]` has nothing to close." |
| `if (x > 5` | E101 | "Left on the stack at the end of the line." |
| `print("if (x > 0)")` | PASSED | "The `if` and the brackets are inside one string token, so no check sees them." |
| `name = "SyntaxLens` | E201 | "No closing quote: the string stops at the end of the line, and the next line is checked normally." |

Tapos C family: **Code Block** → *Load a sample* → **C++ - common mistakes** →
**Analyze** → kusang na-detect ang C++, 10 errors at 1 warning. Ituro ang line 9,
`char grade = 'AB';` → E204: isang character lang dapat ang laman ng character literal.

**Buksan sa code:**
- [`scan()`](../syntaxlens/checks/delimiters.py#L41): yung `stack` na list, yung
  `append` (push), yung `stack[-1]` (yung nasa ibabaw), yung `pop`, at yung loop sa
  dulo na nagre-report ng naiwan.
- [`_check_blocks()`](../syntaxlens/checks/delimiters.py#L94): sa Java, C, C++ at C#,
  ang `{ }` ay tinutugma sa buong file.
- [`_literal_patterns()`](../syntaxlens/lexer.py#L173): yung pattern ng buong string,
  at yung `_OPEN` pattern na humihinto sa dulo ng linya kapag walang pansara.
- [`profiles/cfamily.py`](../syntaxlens/profiles/cfamily.py): profiles ng C, C++ at C#.

**Hand over:** "Gabriel will show how we check operators, and how one engine handles five languages."

### Ariz: kung tanungin ka

- **Q2: Anong data structure?** Stack. Bakit hindi counter lang? Kasi sa counter,
  okay lang ang `([)]` (pantay ang bilang), pero mali ang order. Stack lang ang
  nakakakita ng tamang order at tamang klase ng bracket.
- **Q6: Paano hindi napa-parse ang laman ng string?** Sa regex, inuuna ang string
  pattern bago ang brackets at operators. Kaya pagdating sa `"`, kinukuha agad
  hanggang sa pansarang `"` bilang isang token. Kapag walang pansara, hanggang dulo
  lang ng linya (E201), at normal ang susunod na linya.
- **Paano na-detect ang language?** Kung pinili mo, yun. Kung hindi, file
  extension. Kung wala pa rin, mga clue sa code, hal. `#include <iostream>` = C++,
  `Console.WriteLine` = C#.

### Ariz: checklist

- [ ] I-drawing sa papel yung stack para sa `f(a[0])` at `x = (a[0)]`, step by step.
- [ ] Alam ang codes: E101 hindi naisara, E102 sobrang pansara, E103 hindi tugma,
      E201 hindi naisarang string, E204 maling character literal.
- [ ] Q8: profiles sa [`cfamily.py`](../syntaxlens/profiles/cfamily.py), tapos
      [`scan()`](../syntaxlens/checks/delimiters.py#L41); test:
      [`test_checks_cfamily.py`](../tests/test_checks_cfamily.py).

---

## 5. Gabriel: operators at language rules (2½ min)

**Tanong na sa'yo:** Q3 (`+5` vs `+ *`).

> **Sabihin:** "The operator check is a machine with **two states**: expecting a value,
> or expecting an operator. A name or number moves it to expecting an operator. A
> binary operator like `+` moves it back to expecting a value. If a `+` or `-` comes
> while we are expecting a value, it is a **sign**, which is fine, so `+5` passes. But
> in `20 + * 5`, after the `+` we expect a value and get `*`, which cannot be a sign:
> that is the error."
>
> **Ibig sabihin:** Dalawa lang ang "mood" ng checker: naghihintay ng value, o
> naghihintay ng operator. Pagkatapos ng number o pangalan, operator na ang hinihintay.
> Pagkatapos ng `+`, value na ulit. Kung `+` o `-` ang dumating habang value ang
> hinihintay, sign siya (positive o negative), okay lang. Pero yung `*` hindi pwedeng
> sign, kaya error ang `20 + * 5`.

**Ipakita, part 1 (Single Line, Auto-detect):**

| I-type | Resulta | Sabihin |
|---|---|---|
| `x = +5` | PASSED | "`+` while expecting a value: a sign." |
| `x = -(-5)` | PASSED | "Signs and brackets nest too." |
| `y = 20 + * 5` | E401 | "An operator while expecting a value." |
| `x = 5 +` | E402 | "The line ends while we still expect a value." |
| `x = 5 6` | E403 | "A value while expecting an operator." |
| `5 = x` | E404 | "You cannot assign to a number." |

> **Sabihin:** "We support five languages without writing 'if Java, then ...' in the
> checks. Each language switches rules on or off in one table, `LanguageRules`."
>
> **Ibig sabihin:** Walang "kung Java, gawin ito" sa checks. Bawat language may
> listahan ng rules na naka-on o naka-off.

**Ipakita, part 2 (palitan ang Language menu):**

| Language | I-type | Resulta | Sabihin |
|---|---|---|---|
| C | `int *p = &x;` | PASSED | "C has pointers: `*` and `&` before a name are allowed." |
| C | `int y = 20 + * 5;` | E401 | "But `* 5` is still an error: a pointer needs a name, not a number." |
| Java | `x + 1;` | E406 error | "Java rejects a value that is computed and thrown away." |
| C | `x + 1;` | W406 warning | "C allows it, so it is only a warning." |

**Buksan sa code:**
- Yung explanation sa taas ng [`expressions.py`](../syntaxlens/expressions.py#L1)
  (yung 2 states), tapos [`expression()`](../syntaxlens/expressions.py#L87): yung
  `state == EXPECT_OPERAND` na branch, yung sign check (`self.prefix`), at yung E401.
- [`profiles/rules.py`](../syntaxlens/profiles/rules.py): yung `LanguageRules` table,
  at kung saan naka-on ang `pointer_operators` ng C sa [`cfamily.py`](../syntaxlens/profiles/cfamily.py).
- Yung test na [`test_shared_code_does_not_branch_on_language_names`](../tests/test_language_rules.py#L220):
  magfa-fail siya kapag may nag-check ng pangalan ng language sa shared code.

**Hand over:** "Marco will finish with how the analyzer keeps going after an error."

### Gabriel: kung tanungin ka

- **Q3: `+5` vs `+ *`?** Yung 2 states sa itaas. Sign ang `+` at `-` kapag value
  ang hinihintay; ang `*` hindi pwede.
- **Paano 5 languages sa iisang engine?** Profile (spelling ng language) + rules
  (ano ang pinapayagan). May test na nagbabantay na walang language-name check.
- **Error ba ang `x + 1;`?** Sa Java at C#, oo (E406, "not a statement"). Sa C at
  C++, legal siya, kaya warning lang (W406). Yan yung `discarded_value` rule.

### Gabriel: checklist

- [ ] I-trace sa papel ang `y = 20 + * 5`, token per token, isulat ang state
      pagkatapos ng bawat isa. Ganun din sa `x = +5`.
- [ ] Alam ang codes: E401 dalawang operator, E402 walang value sa dulo, E403 walang
      operator, E404 maling target ng `=`, E406 / W406 value na tinapon.
- [ ] Kaya i-explain ang 3 rules sa `rules.py`, tig-isang sentence (hal.
      `pointer_operators`, `discarded_value`, `type_body_semicolon`).
- [ ] Q8: [`LanguageRules`](../syntaxlens/profiles/rules.py) at yung `_DISCARDED_VALUE`
      table sa [`operators.py`](../syntaxlens/checks/operators.py); test:
      [`test_language_rules.py`](../tests/test_language_rules.py).

---

## Bago mag-present ngayon

1. **Isang buong run-through na may timer** sa presentation laptop, gamit ang `run.bat`.
2. **Quiz sa isa't isa:** bawat isa magtatanong ng 2 tanong sa ibang member mula sa
   "kung tanungin ka" sections. Sagutin nang walang tinitingnan.
3. **Q8 practice:** i-walk through ang sarili mong file nang malakas, 5 minutes bawat isa.
