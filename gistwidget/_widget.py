"""Widget class creation and content extraction."""

from __future__ import annotations

import inspect

import anywidget
import traitlets

from gistwidget._gist import GistFile

JS_FILENAME = "widget.js"
CSS_FILENAME = "widget.css"
PY_FILENAME = "widget.py"


def build_widget_class(
    files: dict[str, GistFile],
    class_name: str = "GistWidget",
) -> type[anywidget.AnyWidget]:
    """Create a widget class from gist files.

    Parameters
    ----------
    files : dict
        Mapping of filename to GistFile.
    class_name : str
        Name for the generated class.
    """

    def _content(key: str) -> str | None:
        f = files.get(key)
        if f is None:
            return None
        return f.content if isinstance(f, GistFile) else str(f)

    js = _content(JS_FILENAME)
    if js is None:
        raise ValueError(f"Gist must contain a {JS_FILENAME} file")
    if not js.strip():
        raise ValueError(f"{JS_FILENAME} must not be empty")

    css = _content(CSS_FILENAME)
    py_source = _content(PY_FILENAME)

    if py_source:
        namespace: dict = {"anywidget": anywidget, "traitlets": traitlets}
        exec(py_source, namespace)  # noqa: S102
        # Find the AnyWidget subclass defined in the source
        widget_cls = None
        for obj in namespace.values():
            if (
                isinstance(obj, type)
                and issubclass(obj, anywidget.AnyWidget)
                and obj is not anywidget.AnyWidget
            ):
                widget_cls = obj
                break
        if widget_cls is None:
            raise ValueError(
                f"{PY_FILENAME} does not define an AnyWidget subclass"
            )
        # Override ESM/CSS with gist content
        widget_cls._esm = js
        if css:
            widget_cls._css = css
        widget_cls.__module__ = "gistwidget"
        return widget_cls

    # No Python source — build a simple dynamic class
    attrs: dict[str, object] = {"_esm": js}
    if css:
        attrs["_css"] = css
    cls = type(class_name, (anywidget.AnyWidget,), attrs)
    cls.__module__ = "gistwidget"
    return cls


def _synthesize_widget_source(cls: type[anywidget.AnyWidget]) -> str | None:
    """Generate Python source that reconstructs the widget's traitlets.

    Returns ``None`` when the class has no custom traits (i.e. only JS/CSS).
    """
    base_trait_names = set(anywidget.AnyWidget.class_trait_names())
    custom_traits = {
        name: cls.class_traits()[name]
        for name in sorted(cls.class_trait_names())
        if name not in base_trait_names
    }
    if not custom_traits:
        return None

    lines = [
        "import anywidget",
        "import traitlets",
        "",
        f"class {cls.__name__}(anywidget.AnyWidget):",
    ]
    for name, trait in custom_traits.items():
        trait_type = type(trait).__name__  # e.g. "Int", "Unicode"
        default = trait.default_value
        tag = trait.metadata
        if tag:
            tag_kwargs = ", ".join(f"{k}={v!r}" for k, v in tag.items())
            lines.append(
                f"    {name} = traitlets.{trait_type}({default!r}).tag({tag_kwargs})"
            )
        else:
            lines.append(f"    {name} = traitlets.{trait_type}({default!r})")
    return "\n".join(lines) + "\n"


def extract_widget_content(widget: type | anywidget.AnyWidget) -> dict[str, str]:
    """Extract file contents from a widget class or instance."""
    cls = widget if isinstance(widget, type) else type(widget)
    # Use the instance for attribute access when available so traitlets
    # descriptors resolve to their values instead of the descriptor object.
    obj = widget

    files: dict[str, str] = {}

    esm = getattr(obj, "_esm", None)
    if esm is not None:
        files[JS_FILENAME] = str(esm)

    css = getattr(obj, "_css", None)
    if css is not None:
        files[CSS_FILENAME] = str(css)

    # Try to get real source code first. inspect.getsource can return wrong
    # content in dynamic contexts (e.g. marimo notebooks), so validate it.
    py_source: str | None = None
    try:
        source = inspect.getsource(cls)
        if f"class {cls.__name__}" in source:
            py_source = source
    except (OSError, TypeError):
        pass

    # Fall back to synthesizing source from traitlets introspection.
    if py_source is None:
        py_source = _synthesize_widget_source(cls)

    if py_source is not None:
        files[PY_FILENAME] = py_source

    return files
