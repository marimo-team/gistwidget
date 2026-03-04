"""GitHub Gist API client using stdlib urllib."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass

API_BASE = "https://api.github.com"


class GistError(Exception):
    """Error from the GitHub Gist API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class GistFile:
    filename: str
    content: str
    language: str | None = None


@dataclass
class GistResult:
    gist_id: str
    html_url: str


def _request(
    method: str,
    url: str,
    token: str | None = None,
    body: dict | None = None,
) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gistwidget",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read()).get("message", str(e))
        except Exception:
            detail = str(e)
        raise GistError(detail, status_code=e.code) from e
    except urllib.error.URLError as e:
        raise GistError(f"Network error: {e.reason}") from e


def _normalize_gist_id(gist_id: str) -> str:
    """Extract the raw gist hash from various input formats.

    Accepts:
      - ``"abc123"``
      - ``"user/abc123"``
      - ``"https://gist.github.com/user/abc123"``
    """
    gist_id = gist_id.strip().rstrip("/")
    # Full URL — take last path segment
    if gist_id.startswith(("https://", "http://")):
        gist_id = gist_id.rsplit("/", 1)[-1]
    # user/hash — take part after slash
    elif "/" in gist_id:
        gist_id = gist_id.rsplit("/", 1)[-1]
    return gist_id


def fetch_gist(gist_id: str, token: str | None = None) -> dict[str, GistFile]:
    if not gist_id:
        raise GistError("gist_id must be a non-empty string")
    gist_id = _normalize_gist_id(gist_id)
    data = _request("GET", f"{API_BASE}/gists/{gist_id}", token=token)
    files: dict[str, GistFile] = {}
    for name, info in data.get("files", {}).items():
        files[name] = GistFile(
            filename=name,
            content=info.get("content", ""),
            language=info.get("language"),
        )
    return files


def create_gist(
    files: dict[str, str],
    description: str = "",
    public: bool = False,
    token: str | None = None,
) -> GistResult:
    if not token:
        raise GistError("Authentication required to create a gist")
    body = {
        "description": description,
        "public": public,
        "files": {name: {"content": content} for name, content in files.items()},
    }
    data = _request("POST", f"{API_BASE}/gists", token=token, body=body)
    return GistResult(gist_id=data["id"], html_url=data["html_url"])


def update_gist(
    gist_id: str,
    files: dict[str, str | None],
    description: str | None = None,
    token: str | None = None,
) -> GistResult:
    """Update a gist. Files mapped to ``None`` are deleted."""
    if not gist_id:
        raise GistError("gist_id must be a non-empty string")
    gist_id = _normalize_gist_id(gist_id)
    if not token:
        raise GistError("Authentication required to update a gist")
    gist_files: dict[str, dict[str, str] | None] = {}
    for name, content in files.items():
        gist_files[name] = {"content": content} if content is not None else None
    body: dict = {"files": gist_files}
    if description is not None:
        body["description"] = description
    data = _request("PATCH", f"{API_BASE}/gists/{gist_id}", token=token, body=body)
    return GistResult(gist_id=data["id"], html_url=data["html_url"])
