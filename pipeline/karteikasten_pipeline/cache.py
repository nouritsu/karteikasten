"""Stage outputs cached in data/work/cache (D48).

Each entry is a pickle named after its stage and a hash of everything it was
computed from: the raw files' hashes in sources.lock.json, the overrides and
settings it reads, and the source code of the modules that compute it. A new
input or a code change gives a new key, so a stale result is never reused; the
older file of the same stage is deleted when the new one is written.
"""

import hashlib
import json
import pickle
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TypeVar

T = TypeVar("T")


def digest(*parts: object) -> str:
    """sha256 of the parts as canonical JSON."""
    text = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode()).hexdigest()


def code(*modules: ModuleType) -> str:
    """sha256 over the source files of the given modules."""
    sha = hashlib.sha256()
    for module in sorted(modules, key=lambda m: m.__name__):
        sha.update(module.__name__.encode())
        assert module.__file__, module
        sha.update(Path(module.__file__).read_bytes())
    return sha.hexdigest()


def files(paths: Iterable[Path]) -> str:
    """sha256 over the names and contents of files (missing ones count as empty)."""
    sha = hashlib.sha256()
    for path in sorted(paths):
        sha.update(path.name.encode())
        sha.update(path.read_bytes() if path.exists() else b"")
    return sha.hexdigest()


@dataclass
class Cache:
    directory: Path
    fresh: bool = False
    log: Callable[[str], None] = print

    def path(self, stage: str, key: str) -> Path:
        return self.directory / f"{stage}-{key[:16]}.pickle"

    def get(self, stage: str, key: str, compute: Callable[[], T]) -> T:
        """The cached result for (stage, key), or compute, store and return it.
        With `fresh`, every stage is computed again (and the cache rewritten)."""
        path = self.path(stage, key)
        if path.exists() and not self.fresh:
            return pickle.loads(path.read_bytes())
        self.log(f"{stage}: computing")
        value = compute()
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        tmp.replace(path)
        for old in self.directory.glob(f"{stage}-*.pickle"):
            if old != path:
                old.unlink()
        return value
