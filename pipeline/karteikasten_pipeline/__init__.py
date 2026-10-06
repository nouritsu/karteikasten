"""Karteikasten data pipeline: source snapshots in data/raw, deck bundles in data/dist/deck."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("karteikasten-pipeline")
except PackageNotFoundError:  # running from the source tree (dev shell, tests)
    __version__ = "0+source"
