import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Publish a Widget to a Gist

    This notebook defines a drawing-canvas widget with multiple
    traitlets and shows how to publish it using `gistwidget.publish()`.
    """)
    return


@app.cell
def _():
    import anywidget
    import traitlets

    class SketchWidget(anywidget.AnyWidget):
        _esm = """
    export default {
      render({ model, el }) {
    // --- DOM setup ---
    const wrapper = document.createElement("div");
    wrapper.className = "sketch-wrapper";

    const toolbar = document.createElement("div");
    toolbar.className = "sketch-toolbar";

    const canvas = document.createElement("canvas");
    canvas.className = "sketch-canvas";
    const ctx = canvas.getContext("2d");

    function resize() {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      redraw();
    }

    // --- Color picker ---
    const colorInput = document.createElement("input");
    colorInput.type = "color";
    colorInput.value = model.get("stroke_color");
    colorInput.title = "Stroke color";
    colorInput.addEventListener("input", (e) => {
      model.set("stroke_color", e.target.value);
      model.save_changes();
    });

    // --- Brush size slider ---
    const sizeLabel = document.createElement("label");
    sizeLabel.className = "sketch-label";
    const sizeSlider = document.createElement("input");
    sizeSlider.type = "range";
    sizeSlider.min = "1";
    sizeSlider.max = "32";
    sizeSlider.value = String(model.get("brush_size"));
    sizeSlider.title = "Brush size";
    sizeSlider.addEventListener("input", (e) => {
      model.set("brush_size", parseInt(e.target.value, 10));
      model.save_changes();
      sizeLabel.textContent = `Size: ${e.target.value}`;
    });
    sizeLabel.textContent = `Size: ${sizeSlider.value}`;

    // --- Tool buttons ---
    function makeBtn(text, title, onClick) {
      const btn = document.createElement("button");
      btn.textContent = text;
      btn.title = title;
      btn.className = "sketch-btn";
      btn.addEventListener("click", onClick);
      return btn;
    }

    const undoBtn = makeBtn("Undo", "Undo last stroke", () => {
      const strokes = model.get("strokes");
      if (strokes.length > 0) {
        model.set("strokes", strokes.slice(0, -1));
        model.save_changes();
      }
    });

    const clearBtn = makeBtn("Clear", "Clear canvas", () => {
      model.set("strokes", []);
      model.save_changes();
    });

    const eraserBtn = makeBtn("Eraser", "Toggle eraser", () => {
      const on = !model.get("eraser");
      model.set("eraser", on);
      model.save_changes();
      eraserBtn.classList.toggle("active", on);
    });

    toolbar.append(colorInput, sizeLabel, sizeSlider, eraserBtn, undoBtn, clearBtn);

    // --- Status bar ---
    const status = document.createElement("div");
    status.className = "sketch-status";
    function updateStatus() {
      const s = model.get("strokes");
      status.textContent = `${s.length} stroke${s.length !== 1 ? "s" : ""}`;
    }
    updateStatus();

    wrapper.append(toolbar, canvas, status);
    el.appendChild(wrapper);

    // --- Drawing logic ---
    let drawing = false;
    let currentStroke = null;

    function getPos(e) {
      const rect = canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return [clientX - rect.left, clientY - rect.top];
    }

    function startDraw(e) {
      e.preventDefault();
      drawing = true;
      const [x, y] = getPos(e);
      currentStroke = {
        color: model.get("eraser") ? "#ffffff" : model.get("stroke_color"),
        size: model.get("brush_size"),
        points: [[x, y]],
      };
    }

    function moveDraw(e) {
      if (!drawing) return;
      e.preventDefault();
      const [x, y] = getPos(e);
      currentStroke.points.push([x, y]);
      redraw();
      drawStroke(currentStroke);
    }

    function endDraw(e) {
      if (!drawing) return;
      drawing = false;
      if (currentStroke && currentStroke.points.length > 1) {
        model.set("strokes", [...model.get("strokes"), currentStroke]);
        model.save_changes();
      }
      currentStroke = null;
    }

    canvas.addEventListener("mousedown", startDraw);
    canvas.addEventListener("mousemove", moveDraw);
    canvas.addEventListener("mouseup", endDraw);
    canvas.addEventListener("mouseleave", endDraw);
    canvas.addEventListener("touchstart", startDraw, { passive: false });
    canvas.addEventListener("touchmove", moveDraw, { passive: false });
    canvas.addEventListener("touchend", endDraw);

    // --- Rendering ---
    function drawStroke(s) {
      if (s.points.length < 2) return;
      ctx.strokeStyle = s.color;
      ctx.lineWidth = s.size;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.beginPath();
      ctx.moveTo(s.points[0][0], s.points[0][1]);
      for (let i = 1; i < s.points.length; i++) {
        ctx.lineTo(s.points[i][0], s.points[i][1]);
      }
      ctx.stroke();
    }

    function redraw() {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      for (const s of model.get("strokes")) drawStroke(s);
    }

    model.on("change:strokes", () => { redraw(); updateStatus(); });
    model.on("change:stroke_color", () => { colorInput.value = model.get("stroke_color"); });
    model.on("change:brush_size", () => {
      sizeSlider.value = String(model.get("brush_size"));
      sizeLabel.textContent = `Size: ${model.get("brush_size")}`;
    });

    new ResizeObserver(resize).observe(canvas);
    requestAnimationFrame(resize);
      },
    };
        """

        _css = """
    .sketch-wrapper {
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-family: system-ui, sans-serif;
      font-size: 13px;
    }
    .sketch-toolbar {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .sketch-toolbar input[type="color"] {
      width: 32px;
      height: 32px;
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 2px;
      cursor: pointer;
    }
    .sketch-toolbar input[type="range"] {
      width: 100px;
    }
    .sketch-label {
      min-width: 52px;
    }
    .sketch-btn {
      padding: 4px 12px;
      border: 1px solid #ccc;
      border-radius: 4px;
      background: #f8f8f8;
      cursor: pointer;
      font-size: 13px;
    }
    .sketch-btn:hover { background: #eee; }
    .sketch-btn.active {
      background: #333;
      color: #fff;
      border-color: #333;
    }
    .sketch-canvas {
      width: 100%;
      height: 360px;
      border: 1px solid #ccc;
      border-radius: 4px;
      cursor: crosshair;
      touch-action: none;
    }
    .sketch-status {
      color: #888;
      font-size: 12px;
    }
        """

        stroke_color = traitlets.Unicode("#e60000").tag(sync=True)
        brush_size = traitlets.Int(4).tag(sync=True)
        eraser = traitlets.Bool(False).tag(sync=True)
        strokes = traitlets.List([]).tag(sync=True)

    SketchWidget()
    return (SketchWidget,)


@app.cell
def _():
    import os

    import gistwidget

    return gistwidget, os


@app.cell
def _(mo):
    publish = mo.ui.run_button(label="Publish")
    publish
    return (publish,)


@app.cell
def _(SketchWidget, gistwidget, os, publish):
    if publish.value:
        result = gistwidget.publish(
            SketchWidget,
            gist_id="mscolnick/4de49e3627f06804c53d235f004d41c0",
            description="Sketch canvas widget",
            token=os.getenv("GITHUB_TOKEN"),
        )
        print(result.html_url)
    return


if __name__ == "__main__":
    app.run()
