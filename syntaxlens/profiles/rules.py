"""The grammar surface of one language, stored as plain data.

A :class:`~syntaxlens.profiles.base.LanguageProfile` says how a language is *spelled* (keywords,
operators, comments).  :class:`LanguageRules` says what the language *allows*: whether it has
preprocessor lines, whether ``x + 1;`` is a mistake or just a warning, whether ``f(void)`` is a
valid parameter list, and so on.

The shared code in ``structure.py``, ``expressions.py`` and ``checks/`` never asks "is this C#?".
It reads the rules of the profile it was given.  Changing how a language is validated means
changing its rules in ``profiles/cfamily.py``; adding a language means writing its rules there.
"""

from __future__ import annotations

from dataclasses import dataclass

#: What a statement that only computes a value (``x + 1;``) means in a language.
DISCARDED_VALUE_ERROR = "error"      # Java, C#: "not a statement" (E406)
DISCARDED_VALUE_WARNING = "warning"  # C, C++: legal, but probably a mistake (W406)


@dataclass(frozen=True)
class LanguageRules:
    """Per-language validation rules.  The defaults describe a language with no special cases."""

    # ---- how statements are built (structure.py)
    preprocessor_lines: bool = False        # '#include', '#define', '#region' lines (C, C++, C#)
    access_labels: bool = False             # 'public:' / 'private:' / 'protected:' labels (C++)
    stream_chains: bool = False             # 'cout << a << endl' is a call-like statement (C++)
    contextual_modifiers: frozenset[str] = frozenset()  # plain names that act as modifiers (C#)
    await_prefix: bool = False              # 'await' is a prefix operator, not a name (C#)

    # ---- a statement that only computes a value (checks/operators.py)
    discarded_value: str = DISCARDED_VALUE_ERROR
    generic_arguments: bool = False         # read 'Run<int>(x)' as the call 'Run(x)' (C#, C++)
    self_reference_statements: bool = False  # a statement may start with 'this' / 'super' (Java)
    arrow_statements: str | None = None     # a statement containing this token is a lambda (Java '->')
    call_operators: frozenset[str] = frozenset()   # operators allowed inside a call statement
    accessor_names: frozenset[str] = frozenset()   # 'get;' 'set;' 'init;' inside a property (C#)

    # ---- method parameters (checks/control.py)
    void_parameter: bool = False            # 'f(void)' means "no parameters" (C, C++)
    variadic_parameter: bool = False        # 'f(int n, ...)' (C, C++)
    parameter_names_optional: bool = False  # 'int add(int, int);' and 'Point p(1, 2);' (C, C++)
    parameter_modifiers: frozenset[str] = frozenset()  # 'final', 'ref', 'out', 'params', ...

    def __post_init__(self) -> None:
        if self.discarded_value not in (DISCARDED_VALUE_ERROR, DISCARDED_VALUE_WARNING):
            raise ValueError("discarded_value must be 'error' or 'warning', not "
                             f"'{self.discarded_value}'.")


#: A language with no special cases.  Use this as a default argument instead of ``LanguageRules()``.
DEFAULT_RULES = LanguageRules()
