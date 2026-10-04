"""The web server, written as a WSGI application.

WSGI is Python's standard interface between a web server and an application:
the server calls ``app(environ, start_response)`` for every request, where
``environ`` describes the request (method, path, body) and ``start_response``
sends the status and headers.  Python's standard library includes a WSGI
server (``wsgiref``), and Vercel runs WSGI apps too, so no web framework
needs to be installed.

Routes:

    GET  /                 the page (static/index.html)
    GET  /static/...       styles, scripts and the editor
    GET  /api/info         version, supported languages and the size limit
    GET  /api/samples      the demo snippets offered in the page
    POST /api/analyze      analyze code and return the result as JSON

POST /api/analyze takes JSON:

    {"mode": "line" | "block", "code": "x = 10", "language": "auto"}
    {"mode": "file", "filename": "Main.java", "content_base64": "...", "language": "auto"}

A file is sent as base64 bytes so the server can decode it exactly like the
command line does: detecting the encoding and rejecting binary files.  The
reply is the JSON report (report/json_report.py) plus both text reports.
The code is only analyzed, never run.
"""

from __future__ import annotations

import base64
import binascii
import json
import mimetypes
import traceback
from pathlib import Path, PurePosixPath

from .. import __version__
from ..analyzer import analyze
from ..profiles import PROFILES
from ..report.json_report import to_dict
from ..report.text import format_report
from ..source import MAX_INPUT_BYTES, InputError, from_bytes, from_text

STATIC = Path(__file__).parent / "static"
SAMPLES = Path(__file__).resolve().parents[2] / "samples"

#: Largest request accepted: a 2 MB file grows by a third when base64-encoded.
MAX_BODY = MAX_INPUT_BYTES * 4 // 3 + 64 * 1024

#: Demo snippets shown in the page's "Samples" menu: (file in samples/, title).
SAMPLE_FILES = [
    ("spec_example_1.py", "Spec Example 1 - valid Python"),
    ("spec_example_2.py", "Spec Example 2 - three errors"),
    ("errors_demo.py", "Python - one error of each kind"),
    ("HelloWorld.java", "Java - valid program"),
    ("ErrorsDemo.java", "Java - common mistakes"),
]

_TYPES = {".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".svg": "image/svg+xml"}


class HttpError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def app(environ, start_response):
    """Handle one HTTP request (the WSGI entry point)."""
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/") or "/"
    try:
        if path == "/api/analyze":
            if method != "POST":
                raise HttpError("405 Method Not Allowed", "Use POST to analyze code.")
            return _json(start_response, "200 OK", _analyze(environ))
        if path == "/api/info":
            return _json(start_response, "200 OK", _info())
        if path == "/api/samples":
            return _json(start_response, "200 OK", {"samples": _samples()})
        if method not in ("GET", "HEAD"):
            raise HttpError("405 Method Not Allowed", "This address only supports GET.")
        return _static(start_response, path, head=method == "HEAD")
    except HttpError as error:
        return _json(start_response, error.status, {"error": str(error)})
    except Exception:  # never show a stack trace to the browser
        traceback.print_exc()
        return _json(start_response, "500 Internal Server Error",
                     {"error": "Something went wrong on the server. Please try again."})


# ------------------------------------------------------------------- routes

def _analyze(environ) -> dict:
    data = _read_json(environ)
    language = data.get("language", "auto")
    if language not in ("auto", *PROFILES):
        raise HttpError("400 Bad Request", f"Unknown language '{language}'.")
    mode = data.get("mode", "block")
    try:
        if mode == "file":
            name = PurePosixPath(str(data.get("filename") or "upload.txt").replace("\\", "/")).name
            try:
                raw = base64.b64decode(data.get("content_base64", ""), validate=True)
            except (binascii.Error, TypeError) as error:
                raise HttpError("400 Bad Request", "The file content is not valid base64.") from error
            source = from_bytes(raw, name=name or "upload.txt")
        elif mode in ("line", "block"):
            code = data.get("code", "")
            if not isinstance(code, str):
                raise HttpError("400 Bad Request", "'code' must be text.")
            source = from_text(code, name="<single line>" if mode == "line" else "<code block>")
        else:
            raise HttpError("400 Bad Request", "'mode' must be 'line', 'block' or 'file'.")
        if source.is_blank:
            raise InputError(f"{source.name} is empty: there is no code to analyze.")
    except InputError as error:
        raise HttpError("422 Unprocessable Content", str(error)) from error
    result = analyze(source, language)
    payload = to_dict(result)
    payload["mode"] = mode
    payload["report"] = {style: format_report(result, style) for style in ("detailed", "classic")}
    return payload


def _info() -> dict:
    return {
        "name": "SyntaxLens",
        "version": __version__,
        "languages": [{"key": p.key, "name": p.name, "extensions": list(p.extensions)}
                      for p in PROFILES.values()],
        "max_bytes": MAX_INPUT_BYTES,
    }


def _samples() -> list[dict]:
    samples = []
    for filename, title in SAMPLE_FILES:
        path = SAMPLES / filename
        if path.is_file():
            samples.append({
                "id": path.stem,
                "title": title,
                "filename": filename,
                "code": path.read_text(encoding="utf-8"),
            })
    return samples


def _static(start_response, path: str, head: bool):
    """Serve a file from static/, refusing anything outside that folder."""
    relative = "index.html" if path in ("/", "/index.html") else path.removeprefix("/static/")
    if relative == path or ".." in PurePosixPath(relative).parts:
        raise HttpError("404 Not Found", f"Nothing at {path}.")
    file = (STATIC / relative).resolve()
    if not file.is_file() or STATIC.resolve() not in file.parents:
        raise HttpError("404 Not Found", f"Nothing at {path}.")
    body = file.read_bytes()
    content_type = _TYPES.get(file.suffix) or mimetypes.guess_type(file.name)[0] or "application/octet-stream"
    if content_type.startswith("text/"):
        content_type += "; charset=utf-8"
    cache = "public, max-age=86400" if "vendor" in file.parts else "no-cache"
    start_response("200 OK", [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", cache),
        ("X-Content-Type-Options", "nosniff"),
    ])
    return [b"" if head else body]


# ------------------------------------------------------------------ helpers

def _read_json(environ) -> dict:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    if length > MAX_BODY:
        raise HttpError("413 Content Too Large", "The code or file is larger than 2 MB.")
    body = environ["wsgi.input"].read(length) if length else b""
    try:
        data = json.loads(body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HttpError("400 Bad Request", "The request body must be JSON.") from error
    if not isinstance(data, dict):
        raise HttpError("400 Bad Request", "The request body must be a JSON object.")
    return data


def _json(start_response, status: str, data: dict):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ])
    return [body]
