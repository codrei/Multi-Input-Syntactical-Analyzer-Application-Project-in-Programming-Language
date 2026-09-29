# SyntaxLens — Multi-Input Syntactical Analyzer

SyntaxLens checks source code for syntax errors without running it. Code can be
given three ways: a single line, a multi-line block, or an uploaded file.
SyntaxLens splits the code into tokens and checks them against syntax rules. It
then produces a report that either confirms the code is valid or lists each
error with its line number, category and explanation.

**Status:** Phase 1 of 8 (project setup and lexer) is in progress. See the
[project plan](docs/PLAN.md).
