"""Smoke test: verify the package imports and exports are intact."""

from gistwidget import GistError, GistResult, load, publish

assert callable(load)
assert callable(publish)
assert issubclass(GistError, Exception)
print("smoke test passed")
