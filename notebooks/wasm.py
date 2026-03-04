import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
async def _():
    import micropip

    await micropip.install("gistwidget")
    import gistwidget

    return (gistwidget,)


@app.cell
def _(gistwidget):
    Widget = gistwidget.load("4de49e3627f06804c53d235f004d41c0")
    Widget()
    return


if __name__ == "__main__":
    app.run()
