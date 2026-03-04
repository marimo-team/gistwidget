"""Tests for gistwidget._widget."""

from __future__ import annotations

import pytest

import anywidget
import traitlets

from gistwidget._gist import GistFile
from gistwidget._widget import (
    JS_FILENAME,
    CSS_FILENAME,
    PY_FILENAME,
    _synthesize_widget_source,
    build_widget_class,
    extract_widget_content,
)


def _gist_files(**kwargs: str) -> dict[str, GistFile]:
    """Helper to create a files dict from filename=content pairs."""
    return {
        name: GistFile(filename=name, content=content)
        for name, content in kwargs.items()
    }


JS_CODE = "export default { render({ el }) { el.innerText = 'hi'; } };"
CSS_CODE = ".widget { color: red; }"
PY_CODE = """\
import anywidget
import traitlets

class Counter(anywidget.AnyWidget):
    count = traitlets.Int(0).tag(sync=True)
"""


class TestBuildWidgetClass:
    def test_js_only(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE})
        cls = build_widget_class(files)
        assert issubclass(cls, anywidget.AnyWidget)
        assert cls._esm == JS_CODE
        assert cls.__module__ == "gistwidget"

    def test_js_and_css(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE, CSS_FILENAME: CSS_CODE})
        cls = build_widget_class(files)
        assert cls._esm == JS_CODE
        assert cls._css == CSS_CODE

    def test_js_css_python(self):
        files = _gist_files(
            **{JS_FILENAME: JS_CODE, CSS_FILENAME: CSS_CODE, PY_FILENAME: PY_CODE}
        )
        cls = build_widget_class(files)
        assert issubclass(cls, anywidget.AnyWidget)
        assert cls._esm == JS_CODE
        assert cls._css == CSS_CODE
        assert cls.__module__ == "gistwidget"

    def test_missing_js(self):
        files = _gist_files(**{CSS_FILENAME: CSS_CODE})
        with pytest.raises(ValueError, match="widget.js"):
            build_widget_class(files)

    def test_empty_js(self):
        files = _gist_files(**{JS_FILENAME: "   "})
        with pytest.raises(ValueError, match="must not be empty"):
            build_widget_class(files)

    def test_python_without_subclass(self):
        bad_py = "x = 42\n"
        files = _gist_files(**{JS_FILENAME: JS_CODE, PY_FILENAME: bad_py})
        with pytest.raises(ValueError, match="does not define an AnyWidget subclass"):
            build_widget_class(files)

    def test_custom_class_name(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE})
        cls = build_widget_class(files, class_name="MyWidget")
        assert cls.__name__ == "MyWidget"


class TestExtractWidgetContent:
    def test_from_class(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE, CSS_FILENAME: CSS_CODE})
        cls = build_widget_class(files)
        content = extract_widget_content(cls)
        assert content[JS_FILENAME] == JS_CODE
        assert content[CSS_FILENAME] == CSS_CODE

    def test_from_instance(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE})
        cls = build_widget_class(files)
        instance = cls()
        content = extract_widget_content(instance)
        assert content[JS_FILENAME] == JS_CODE

    def test_round_trip(self):
        files = _gist_files(**{JS_FILENAME: JS_CODE, CSS_FILENAME: CSS_CODE})
        cls = build_widget_class(files)
        content = extract_widget_content(cls)
        assert content[JS_FILENAME] == JS_CODE
        assert content[CSS_FILENAME] == CSS_CODE

    def test_no_py_for_js_only_widget(self):
        """A dynamic class with no custom traits should not produce widget.py."""
        files = _gist_files(**{JS_FILENAME: JS_CODE})
        cls = build_widget_class(files)
        content = extract_widget_content(cls)
        assert PY_FILENAME not in content

    def test_synthesize_with_traitlets(self):
        """A dynamic class with custom traitlets should produce widget.py."""
        files = _gist_files(**{JS_FILENAME: JS_CODE, PY_FILENAME: PY_CODE})
        cls = build_widget_class(files)
        content = extract_widget_content(cls)
        assert PY_FILENAME in content
        py = content[PY_FILENAME]
        assert "class Counter(anywidget.AnyWidget):" in py
        assert "traitlets.Int(0)" in py
        assert "sync=True" in py


class TestSynthesizeWidgetSource:
    def test_no_custom_traits(self):
        cls = type("W", (anywidget.AnyWidget,), {"_esm": "x"})
        assert _synthesize_widget_source(cls) is None

    def test_with_traits(self):
        cls = type(
            "Counter",
            (anywidget.AnyWidget,),
            {
                "_esm": "x",
                "count": traitlets.Int(0).tag(sync=True),
                "label": traitlets.Unicode("hi"),
            },
        )
        source = _synthesize_widget_source(cls)
        assert source is not None
        assert "class Counter(anywidget.AnyWidget):" in source
        assert "count = traitlets.Int(0).tag(sync=True)" in source
        assert "label = traitlets.Unicode('hi')" in source

    def test_round_trip_exec(self):
        """Synthesized source should be executable and recreate the class."""
        cls = type(
            "MyWidget",
            (anywidget.AnyWidget,),
            {
                "_esm": "x",
                "value": traitlets.Float(3.14).tag(sync=True),
            },
        )
        source = _synthesize_widget_source(cls)
        ns: dict = {"anywidget": anywidget, "traitlets": traitlets}
        exec(source, ns)  # noqa: S102
        rebuilt = ns["MyWidget"]
        assert issubclass(rebuilt, anywidget.AnyWidget)
        assert "value" in rebuilt.class_trait_names()
