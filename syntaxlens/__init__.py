"""SyntaxLens: a multi-input syntactical analyzer.

The analysis runs as a pipeline of small stages, one module each:

    source.py   load the input (single line, code block or file) and clean it up
    detect.py   decide which language's rules apply
    lexer.py    split the text into tokens (token types live in tokens.py)

The statement builder, the eight syntax checks and the full report are added
in later phases (see docs/PLAN.md).  The engine uses only the Python standard
library, so every step can be read without knowing any third-party package.
"""

__version__ = "0.1.0"
