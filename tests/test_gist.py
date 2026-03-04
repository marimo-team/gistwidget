"""Tests for gistwidget._gist."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock

import pytest

from gistwidget._gist import (
    GistError,
    GistFile,
    GistResult,
    _normalize_gist_id,
    _request,
    create_gist,
    fetch_gist,
    update_gist,
)


# --- dataclass construction ---


class TestDataclasses:
    def test_gist_error_with_status(self):
        err = GistError("bad", status_code=404)
        assert str(err) == "bad"
        assert err.status_code == 404

    def test_gist_error_without_status(self):
        err = GistError("oops")
        assert err.status_code is None

    def test_gist_file(self):
        f = GistFile(filename="a.js", content="code", language="JavaScript")
        assert f.filename == "a.js"
        assert f.content == "code"
        assert f.language == "JavaScript"

    def test_gist_result(self):
        r = GistResult(gist_id="abc", html_url="https://gist.github.com/abc")
        assert r.gist_id == "abc"


# --- _normalize_gist_id ---


class TestNormalizeGistId:
    def test_plain_hash(self):
        assert _normalize_gist_id("abc123") == "abc123"

    def test_user_slash_hash(self):
        assert _normalize_gist_id("user/abc123") == "abc123"

    def test_full_url(self):
        assert _normalize_gist_id("https://gist.github.com/user/abc123") == "abc123"

    def test_trailing_slash(self):
        assert _normalize_gist_id("user/abc123/") == "abc123"

    def test_whitespace(self):
        assert _normalize_gist_id("  abc123  ") == "abc123"


# --- _request ---


class TestRequest:
    def test_success(self, mock_urlopen, monkeypatch):
        mock_urlopen({"ok": True})
        result = _request("GET", "https://api.github.com/gists/123")
        assert result == {"ok": True}

    def test_with_token(self, mock_urlopen, monkeypatch):
        mock_urlopen({"ok": True})
        captured = {}

        original = __import__("urllib.request", fromlist=["Request"]).Request

        class CapturingRequest(original):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                captured["headers"] = dict(self.headers)

        monkeypatch.setattr("urllib.request.Request", CapturingRequest)
        _request("GET", "https://api.github.com/gists/123", token="ghp_test")
        assert captured["headers"].get("Authorization") == "token ghp_test"

    def test_with_body(self, mock_urlopen, monkeypatch):
        mock_urlopen({"id": "new"})
        captured = {}

        original = __import__("urllib.request", fromlist=["Request"]).Request

        class CapturingRequest(original):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                captured["data"] = self.data

        monkeypatch.setattr("urllib.request.Request", CapturingRequest)
        _request("POST", "https://api.github.com/gists", body={"files": {}})
        assert json.loads(captured["data"]) == {"files": {}}

    def test_http_error(self, monkeypatch):
        def raise_http_error(req):
            body = json.dumps({"message": "Not Found"}).encode()
            raise urllib.error.HTTPError(
                url="https://api.github.com/gists/bad",
                code=404,
                msg="Not Found",
                hdrs={},
                fp=MagicMock(read=MagicMock(return_value=body)),
            )

        monkeypatch.setattr("urllib.request.urlopen", raise_http_error)
        with pytest.raises(GistError, match="Not Found") as exc_info:
            _request("GET", "https://api.github.com/gists/bad")
        assert exc_info.value.status_code == 404

    def test_url_error(self, monkeypatch):
        def raise_url_error(req):
            raise urllib.error.URLError("Name or service not known")

        monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
        with pytest.raises(GistError, match="Network error"):
            _request("GET", "https://api.github.com/gists/123")


# --- fetch_gist ---


class TestFetchGist:
    def test_success(self, mock_urlopen):
        mock_urlopen(
            {
                "files": {
                    "widget.js": {
                        "content": "export default {};",
                        "language": "JavaScript",
                    }
                }
            }
        )
        files = fetch_gist("abc123")
        assert "widget.js" in files
        assert files["widget.js"].content == "export default {};"

    def test_empty_gist_id(self):
        with pytest.raises(GistError, match="non-empty"):
            fetch_gist("")


# --- create_gist ---


class TestCreateGist:
    def test_success(self, mock_urlopen):
        mock_urlopen({"id": "new123", "html_url": "https://gist.github.com/new123"})
        result = create_gist(
            {"widget.js": "export default {};"}, token="ghp_test"
        )
        assert result.gist_id == "new123"

    def test_no_token(self):
        with pytest.raises(GistError, match="Authentication required"):
            create_gist({"widget.js": "code"})


# --- update_gist ---


class TestUpdateGist:
    def test_success(self, mock_urlopen):
        mock_urlopen({"id": "abc", "html_url": "https://gist.github.com/abc"})
        result = update_gist("abc", {"widget.js": "code"}, token="ghp_test")
        assert result.gist_id == "abc"

    def test_no_token(self):
        with pytest.raises(GistError, match="Authentication required"):
            update_gist("abc", {"widget.js": "code"})

    def test_empty_gist_id(self):
        with pytest.raises(GistError, match="non-empty"):
            update_gist("", {"widget.js": "code"}, token="ghp_test")
