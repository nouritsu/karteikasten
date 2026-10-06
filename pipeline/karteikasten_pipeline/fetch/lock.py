"""sources.lock.json: for every raw file, where it came from, when, its size and hash.

Kaikki and Tatoeba publish weekly at unversioned URLs, so the lock (together with
the snapshot in data/raw) is what makes a build reproducible.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Entry:
    source: str
    url: str
    retrieved_at: str
    bytes: int
    sha256: str


def load(path: Path) -> dict[str, Entry]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported schema_version {data.get('schema_version')!r}")
    return {name: Entry(**entry) for name, entry in data["files"].items()}


def save(path: Path, entries: dict[str, Entry]) -> None:
    data = {
        "schema_version": SCHEMA_VERSION,
        "files": {name: asdict(entries[name]) for name in sorted(entries)},
    }
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
