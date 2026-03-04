"""Tests for gistwidget public API."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

import anywidget
import traitlets

import gistwidget
from gistwidget import GistError, GistResult, load, publish


FAKE_GIST_RESPONSE = {
    "id": "abc123",
    "html_url": "https://gist.github.com/abc123",
    "files": {
        "widget.js": {
            "content": "export default { render({ el }) { el.innerText = 'hi'; } };",
            "language": "JavaScript",
        }
    },
}


class TestLoad:
    def test_success(self, mock_urlopen):
        mock_urlopen(FAKE_GIST_RESPONSE)
        cls = load("abc123")
        assert issubclass(cls, anywidget.AnyWidget)

    def test_empty_gist_id(self):
        with pytest.raises(GistError, match="non-empty"):
            load("")


class TestPublish:
    def test_create(self, mock_urlopen):
        mock_urlopen({"id": "new1", "html_url": "https://gist.github.com/new1"})

        class W(anywidget.AnyWidget):
            _esm = "export default {};"

        result = publish(W, token="ghp_test")
        assert isinstance(result, GistResult)
        assert result.gist_id == "new1"

    def test_update(self, monkeypatch):
        # publish with gist_id makes two calls: GET (fetch existing) then PATCH (update).
        responses = [
            # First call: fetch existing gist (has widget.js + widget.py)
            {
                "id": "existing",
                "html_url": "https://gist.github.com/existing",
                "files": {
                    "widget.js": {"content": "old;", "language": "JavaScript"},
                    "widget.py": {"content": "old", "language": "Python"},
                },
            },
            # Second call: update result
            {"id": "existing", "html_url": "https://gist.github.com/existing"},
        ]
        call_index = {"i": 0}
        captured_requests: list[object] = []

        def fake_urlopen(req):
            idx = call_index["i"]
            call_index["i"] += 1
            captured_requests.append(req)
            body = json.dumps(responses[idx]).encode()
            resp = MagicMock()
            resp.read.return_value = body
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        # Use a dynamic class so inspect.getsource won't find widget.py source
        W = type("W", (anywidget.AnyWidget,), {"_esm": "export default {};"})

        result = publish(W, gist_id="existing", token="ghp_test")
        assert result.gist_id == "existing"

        # The PATCH request should delete widget.py (set to null)
        patch_req = captured_requests[1]
        patch_body = json.loads(patch_req.data)
        assert patch_body["files"]["widget.py"] is None
        assert patch_body["files"]["widget.js"]["content"] == "export default {};"

    def test_no_esm_error(self):
        class BadWidget(anywidget.AnyWidget):
            pass

        with pytest.raises(GistError, match="_esm"):
            publish(BadWidget, token="ghp_test")


class TestEnvVarsNotAutoRead:
    def test_no_auto_env_resolution(self, monkeypatch, mock_urlopen):
        """Ensure that setting GITHUB_TOKEN env var does NOT auto-authenticate."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")
        mock_urlopen(FAKE_GIST_RESPONSE)

        # load() should pass token=None through, not pick up the env var
        cls = load("abc123")
        assert issubclass(cls, anywidget.AnyWidget)

        # publish create should still require explicit token
        class W(anywidget.AnyWidget):
            _esm = "export default {};"

        with pytest.raises(GistError, match="Authentication required"):
            publish(W)


class TestExports:
    def test_all_exports(self):
        assert "load" in gistwidget.__all__
        assert "publish" in gistwidget.__all__
        assert "GistResult" in gistwidget.__all__
        assert "GistError" in gistwidget.__all__
