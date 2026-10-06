"""Locating the working tree the pipeline reads and writes.

`nix run` executes the CLI from the Nix store, and data/ is gitignored, so the
flake source never contains it. The CLI therefore works on the checkout it is
started from, recognised by its config file.
"""

from dataclasses import dataclass
from pathlib import Path

MARKER = Path("config/pipeline.toml")


class NotInWorkingTree(Exception):
    pass


def find_root(start: Path) -> Path:
    """Return the nearest directory at or above `start` that holds config/pipeline.toml."""
    start = start.resolve()
    for directory in (start, *start.parents):
        if (directory / MARKER).is_file():
            return directory
    raise NotInWorkingTree(f"no {MARKER} in {start} or any parent; run this inside the karteikasten checkout")


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def config(self) -> Path:
        return self.root / MARKER

    @property
    def lock(self) -> Path:
        return self.root / "sources.lock.json"

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def work(self) -> Path:
        return self.root / "data" / "work"

    @property
    def dist(self) -> Path:
        return self.root / "data" / "dist"

    @property
    def overrides(self) -> Path:
        return self.root / "overrides"

    @property
    def reports(self) -> Path:
        return self.root / "reports"
