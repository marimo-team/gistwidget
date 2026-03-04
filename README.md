# gistwidget

> **Labs** — This is an experimental project. And not recommended for production use.

Share [anywidgets](https://anywidget.dev) via GitHub Gists. Two functions, zero config.

Build a widget in a notebook, publish it to a gist, and anyone can load it back — JS, CSS, Python traitlets and all.

## Install

```
uv add gistwidget
# or
pip install gistwidget
```

## Quickstart

**Load** a widget someone already published:

```python
import gistwidget

Widget = gistwidget.load("4de49e3627f06804c53d235f004d41c0")
Widget()
```

**Publish** your own:

```python
import os
import anywidget
import traitlets
import gistwidget

class CounterWidget(anywidget.AnyWidget):
    _esm = """
    export default {
      render({ model, el }) {
        let btn = document.createElement("button");
        btn.innerText = `Count: ${model.get("count")}`;
        btn.addEventListener("click", () => {
          model.set("count", model.get("count") + 1);
          model.save_changes();
        });
        model.on("change:count", () => {
          btn.innerText = `Count: ${model.get("count")}`;
        });
        el.appendChild(btn);
      }
    };
    """
    count = traitlets.Int(0).tag(sync=True)

result = gistwidget.publish(
    CounterWidget,
    description="Counter widget",
    token=os.getenv("GITHUB_TOKEN"),
)
print(result.html_url)
```

## API

### `gistwidget.load(gist_id, *, token=None)`

Load a widget class from a GitHub Gist.

| Parameter | Type | Description |
|-----------|------|-------------|
| `gist_id` | `str` | Gist ID, `user/id`, or full URL |
| `token` | `str \| None` | GitHub token (only needed for private gists) |

**Returns** a `type[anywidget.AnyWidget]` — the widget *class*, not an instance. Call it to create one.

### `gistwidget.publish(widget, *, gist_id=None, description="", public=False, token=None)`

Publish a widget to a GitHub Gist.

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `type \| instance` | An AnyWidget class or instance |
| `gist_id` | `str \| None` | Update an existing gist (omit to create new) |
| `description` | `str` | Gist description |
| `public` | `bool` | Public or secret gist |
| `token` | `str` | GitHub token (**required**) |

**Returns** a `GistResult` with `.gist_id` and `.html_url`.

### `GistResult`

```python
@dataclass
class GistResult:
    gist_id: str
    html_url: str
```

### `GistError`

Raised on API errors or invalid input. Has an optional `.status_code` attribute for HTTP errors.

## What gets stored in the gist

| File | Contents | When |
|------|----------|------|
| `widget.js` | Your `_esm` JavaScript | Always |
| `widget.css` | Your `_css` stylesheet | If `_css` is set |
| `widget.py` | Traitlet definitions | If the widget has custom traitlets |

When loading, all three are reassembled into a working widget class.

## Notebooks

The `notebooks/` directory contains [marimo](https://marimo.io) notebooks:

- **`load_widget.py`** — Interactive loader: paste a gist ID, get a live widget
- **`publish_widget.py`** — Defines a drawing-canvas widget and publishes it

## Development

```bash
uv pip install -e ".[dev]"
pytest tests/
```
