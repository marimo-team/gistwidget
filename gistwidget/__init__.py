"""gistwidget — Share anywidgets via GitHub Gists."""

from __future__ import annotations

import anywidget

from gistwidget._gist import (
    GistError,
    GistResult,
    create_gist,
    fetch_gist,
    update_gist,
)
from gistwidget._widget import JS_FILENAME, extract_widget_content, build_widget_class

__all__ = ["load", "publish", "GistResult", "GistError"]


def load(
    gist_id: str,
    *,
    token: str | None = None,
) -> type[anywidget.AnyWidget]:
    """Load an anywidget class from a GitHub Gist.

    Parameters
    ----------
    gist_id : str
        The GitHub Gist ID.
    token : str, optional
        GitHub personal access token. Use ``token=os.getenv("GITHUB_TOKEN")``
        to read from an environment variable.

    Returns
    -------
    type[anywidget.AnyWidget]
        The widget **class** (not an instance).
    """
    if not gist_id:
        raise GistError("gist_id must be a non-empty string")
    files = fetch_gist(gist_id, token=token)
    return build_widget_class(files)


def publish(
    widget: type[anywidget.AnyWidget] | anywidget.AnyWidget,
    *,
    gist_id: str | None = None,
    description: str = "",
    public: bool = False,
    token: str | None = None,
) -> GistResult:
    """Publish a widget to a GitHub Gist.

    Parameters
    ----------
    widget : type or instance
        An AnyWidget class or instance.
    gist_id : str, optional
        If provided, updates the existing gist. Otherwise creates a new one.
    description : str
        Gist description.
    public : bool
        Whether the gist is public.
    token : str, optional
        GitHub personal access token. Use ``token=os.getenv("GITHUB_TOKEN")``
        to read from an environment variable.

    Returns
    -------
    GistResult
        Contains ``gist_id`` and ``html_url``.
    """
    files = extract_widget_content(widget)
    if JS_FILENAME not in files:
        raise GistError("Widget must have an _esm attribute with JavaScript content")

    if gist_id:
        # Fetch existing files so we can delete any that are no longer needed.
        existing = fetch_gist(gist_id, token=token)
        merged: dict[str, str | None] = dict(files)
        for name in existing:
            if name not in files:
                merged[name] = None  # tells GitHub API to delete the file
        return update_gist(gist_id, merged, description=description, token=token)
    return create_gist(files, description=description, public=public, token=token)
