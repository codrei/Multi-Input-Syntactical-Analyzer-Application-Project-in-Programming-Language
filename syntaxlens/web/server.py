"""Run the web app on this computer: ``python -m syntaxlens web``.

Uses the WSGI server from Python's standard library (wsgiref), with one
thread per request so the page's files load in parallel.  The address is
127.0.0.1 (this computer only), so nothing is exposed to the network.  If the
port is taken, the next free one is used.
"""

from __future__ import annotations

import threading
import webbrowser
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from .app import app


class _ThreadingServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):  # noqa: A002 - signature from the standard library
        pass  # keep the console clean; errors are still printed by the app


def serve(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> int:
    for candidate in range(port, port + 20):
        try:
            server = make_server(host, candidate, app, server_class=_ThreadingServer,
                                 handler_class=_QuietHandler)
            break
        except OSError:
            continue
    else:
        print(f"syntaxlens: ports {port}-{port + 19} are all in use.")
        return 2
    url = f"http://{host}:{candidate}/"
    print(f"SyntaxLens web app running at {url}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0
