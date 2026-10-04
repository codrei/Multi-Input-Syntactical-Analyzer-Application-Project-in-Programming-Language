"""Entry point for Vercel: the SyntaxLens web app as a WSGI application.

Vercel loads the ``app`` variable from this file (see vercel.json).  To run the
same web app on your own computer instead, use:  python -m syntaxlens web
"""

from syntaxlens.web.app import app

__all__ = ["app"]
