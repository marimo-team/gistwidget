"""Shared test fixtures."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def mock_urlopen(monkeypatch):
    """Return a helper that patches urllib.request.urlopen to return *data*."""

    def _setup(data: dict, status: int = 200):
        body = json.dumps(data).encode()
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr("urllib.request.urlopen", lambda req: resp)
        return resp

    return _setup
