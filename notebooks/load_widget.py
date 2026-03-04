import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    gist_id_input = mo.ui.text(
        label="Gist ID",
        placeholder="paste a gist ID here",
        value="mscolnick/4de49e3627f06804c53d235f004d41c0",
    )
    gist_id_input
    return (gist_id_input,)


@app.cell
def _(gist_id_input, mo):
    import gistwidget
    mo.stop(not gist_id_input.value)

    # Only load when a gist ID is provided
    Widget = gistwidget.load(gist_id_input.value)
    return (Widget,)


@app.cell
def _(Widget):
    widget = Widget()
    widget
    return


if __name__ == "__main__":
    app.run()
