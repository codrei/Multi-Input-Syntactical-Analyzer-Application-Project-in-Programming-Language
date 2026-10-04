"""The web app's server side, called directly as a WSGI application."""

import base64
import io
import json
from pathlib import Path
from wsgiref.util import setup_testing_defaults

import pytest

import app as vercel_entry
from syntaxlens.web.app import MAX_BODY, app

SAMPLES = Path(__file__).parent.parent / "samples"


def request(method, path, body=None):
    """Send one request to the app; return (status code, headers, body bytes)."""
    raw = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(raw)),
               "CONTENT_TYPE": "application/json", "wsgi.input": io.BytesIO(raw)}
    setup_testing_defaults(environ)
    captured = {}

    def start_response(status, headers):
        captured["status"], captured["headers"] = int(status.split()[0]), dict(headers)

    content = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], content


def analyze(**payload):
    status, _, content = request("POST", "/api/analyze", payload)
    return status, json.loads(content)


def test_vercel_entry_point_is_the_same_app():
    assert vercel_entry.app is app


def test_page_and_static_files_are_served():
    status, headers, content = request("GET", "/")
    assert status == 200 and headers["Content-Type"].startswith("text/html")
    assert b"SyntaxLens" in content
    for path in ("/static/app.js", "/static/styles.css", "/static/vendor/codemirror/codemirror.min.js"):
        assert request("GET", path)[0] == 200


@pytest.mark.parametrize("path", ["/static/../app.py", "/static/missing.js", "/app.py", "/secret"])
def test_nothing_outside_the_static_folder_is_served(path):
    assert request("GET", path)[0] == 404


def test_info_and_samples():
    _, _, content = request("GET", "/api/info")
    info = json.loads(content)
    assert {language["key"] for language in info["languages"]} == {"python", "java"}
    _, _, content = request("GET", "/api/samples")
    ids = [sample["id"] for sample in json.loads(content)["samples"]]
    assert ids[:2] == ["spec_example_1", "spec_example_2"]


def test_single_line_mode():
    status, data = analyze(mode="line", code="y = 20 + * 5", language="auto")
    assert status == 200
    assert data["status"] == "FAILED"
    assert data["diagnostics"][0]["code"] == "E401"
    assert data["mode"] == "line"
    assert set(data["report"]) == {"detailed", "classic"}


def test_code_block_mode_reproduces_spec_example_2():
    from tests.test_spec_examples import EXAMPLE_2_REPORT

    code = (SAMPLES / "spec_example_2.py").read_text(encoding="utf-8")
    status, data = analyze(mode="block", code=code, language="python")
    assert status == 200
    expected = EXAMPLE_2_REPORT.replace(
        "Python (auto-detected from the .py extension)", "Python (selected by the user)")
    assert data["report"]["classic"] == expected


def test_file_mode_uses_the_file_name_and_bytes():
    content = base64.b64encode((SAMPLES / "HelloWorld.java").read_bytes()).decode()
    status, data = analyze(mode="file", filename="HelloWorld.java", content_base64=content)
    assert status == 200
    assert data["status"] == "PASSED"
    assert data["language"]["description"] == "Java (auto-detected from the .java extension)"


def test_windows_file_with_crlf_and_folders_in_the_name():
    content = base64.b64encode(b"x = 10\r\nif x > 5\r\n    print(x)\r\n").decode()
    status, data = analyze(mode="file", filename="C:\\Users\\me\\demo.py", content_base64=content)
    assert status == 200
    assert data["source"]["name"] == "demo.py"
    assert data["source"]["line_endings"] == "CRLF"
    assert [d["code"] for d in data["diagnostics"]] == ["E302"]


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({"mode": "block", "code": "   "}, 422, "empty"),
        ({"mode": "file", "filename": "x.png",
          "content_base64": base64.b64encode(b"\x89PNG\r\n\x1a\n\x00\x00").decode()}, 422, "binary"),
        ({"mode": "file", "filename": "x.py", "content_base64": "@@not base64@@"}, 400, "base64"),
        ({"mode": "line", "code": "x", "language": "cobol"}, 400, "Unknown language"),
        ({"mode": "voice", "code": "x"}, 400, "mode"),
        ({"mode": "line", "code": 42}, 400, "text"),
    ],
)
def test_bad_requests_get_clear_messages(payload, status, message):
    got_status, data = analyze(**payload)
    assert got_status == status
    assert message in data["error"]


def test_body_must_be_json_and_method_must_be_post():
    assert request("POST", "/api/analyze", b"not json")[0] == 400
    assert request("GET", "/api/analyze")[0] == 405
    assert request("DELETE", "/")[0] == 405


def test_oversized_body_is_refused():
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/analyze",
               "CONTENT_LENGTH": str(MAX_BODY + 1), "wsgi.input": io.BytesIO(b"")}
    setup_testing_defaults(environ)
    statuses = []
    app(environ, lambda status, headers: statuses.append(status))
    assert statuses[0].startswith("413")
