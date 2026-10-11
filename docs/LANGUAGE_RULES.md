# Per-language rules

A language profile (`syntaxlens/profiles/`) has two parts:

* **spelling** — keywords, operators, comments, literals: what the *lexer* needs;
* **rules** (`LanguageRules`, in `profiles/rules.py`) — what the language *allows*.

The shared code never tests for a language name. It reads `profile.rules`. A test
(`tests/test_language_rules.py`) fails if `structure.py`, `expressions.py` or a check
starts comparing `profile.key` again.

## Rules by language

| Rule | Python | Java | C | C++ | C# |
|---|---|---|---|---|---|
| `preprocessor_lines` (`#include`, `#define`, `#region`) | – | – | yes | yes | yes |
| `access_labels` (`public:`) | – | – | – | yes | – |
| `stream_chains` (`cout << a << endl`) | – | – | – | yes | – |
| `contextual_modifiers` (`async`, `partial`, `global`) | – | – | – | – | yes |
| `await_prefix` | – | – | – | – | yes |
| `pointer_operators` (`*p`, `&x`; `20 + * 5` is still an error) | – | – | yes | yes | – |
| `arrow_member_access` (`node->next`) | – | – | yes | yes | – |
| `brace_initialization` (`Point p{1, 2};`, `return {x, y};`) | – | – | – | yes | – |
| `property_initializers` (`int X { get; set; } = 5;`) | – | – | – | – | yes |
| `discarded_value` (`x + 1;`) | – | error | warning | warning | error |
| `generic_arguments` (`Run<int>(x)` is a call) | – | – | – | yes | yes |
| `self_reference_statements` (`this.f();`) | – | yes | – | – | – |
| `arrow_statements` (lambda `->`) | – | `->` | – | – | – |
| `accessor_names` (`get;` `set;`) | – | – | – | – | yes |
| `void_parameter` (`f(void)`) | – | – | yes | yes | – |
| `variadic_parameter` (`f(int n, ...)`) | – | – | yes | yes | – |
| `parameter_names_optional` (`int add(int, int);`) | – | – | yes | yes | – |
| `parameter_modifiers` | – | `final` | – | – | `ref out in params this` |

`discarded_value` is `"error"` (E406, the code does not compile) or `"warning"` (W406, legal but
probably a mistake).

## Dispatch

Where the *behavior* differs, a check picks its handler from a table keyed by a rule value:

| Check | Table | Keyed by |
|---|---|---|
| 4 operators | `_DISCARDED_VALUE` in `checks/operators.py` | `rules.discarded_value` |

Where only a detail differs (parameters in `checks/control.py`, statement kinds in
`structure.py`, pointer operators in `expressions.py`), the code reads the individual rule.

C++ raw strings (`R"(C:\path)"`) are a matter of spelling, not of rules, so they are switched on
in the C++ profile itself (`raw_strings=True`) and read by the lexer.

## Adding a language

1. Write its spelling in `profiles/<name>.py` and register it in `profiles/__init__.py`.
2. Give it a `LanguageRules(...)` that turns on what it needs; the defaults mean "no special cases".
3. Add a valid program under `tests/data/<name>_valid/`.
