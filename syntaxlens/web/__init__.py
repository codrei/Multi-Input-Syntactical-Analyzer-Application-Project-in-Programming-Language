"""The SyntaxLens web app: a browser interface for the three input modes.

    app.py      the server side: a WSGI application (standard library only)
    server.py   runs the app on this computer: ``python -m syntaxlens web``
    static/     the page itself: index.html, styles.css, app.js and the
                CodeMirror editor (stored here, so no internet is needed)

The same ``app`` also runs on Vercel (see app.py and vercel.json at the root
of the repository).
"""
