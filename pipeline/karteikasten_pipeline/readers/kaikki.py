"""Kaikki (wiktextract) dumps: one JSON entry per line, all languages mixed.

Stage 20 only needs the German entries. The English dump is 24 GB of JSON, so the
German subset of each edition is extracted once into data/work and reused.
"""

import gzip
import json
from collections.abc import Iterator
from pathlib import Path

# Pre-filter on the raw line before parsing. English entries also contain
# "lang_code": "de" inside their translation lists, so every candidate is parsed
# and checked at the top level.
NEEDLE = '"lang_code": "de"'


def german_entries(dump: Path) -> Iterator[dict]:
    with gzip.open(dump, "rt", encoding="utf-8") as lines:
        for line in lines:
            if NEEDLE not in line:
                continue
            entry = json.loads(line)
            if entry.get("lang_code") == "de":
                yield entry


def extract_german(dump: Path, dest: Path) -> int:
    """Write the German entries of `dump` to `dest` (JSONL) and return how many there were."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8") as out:
        for entry in german_entries(dump):
            out.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            out.write("\n")
            count += 1
    tmp.replace(dest)
    return count


def read(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            yield json.loads(line)


def read_with_offsets(path: Path) -> Iterator[tuple[int, dict]]:
    """Each entry with the byte offset of its line, for an `Index`."""
    offset = 0
    with path.open("rb") as lines:
        for line in lines:
            yield offset, json.loads(line)
            offset += len(line)


class Index:
    """Byte offsets of an extract's entries by key, so later stages read only the
    entries they need instead of the whole file again."""

    def __init__(self, path: Path, offsets: dict[str, list[int]]):
        self.path = path
        self.offsets = offsets

    def get(self, keys: Iterator[str] | list[str] | set[str]) -> dict[str, list[dict]]:
        """Entries per key, in file order; keys without entries are left out."""
        found: dict[str, list[dict]] = {}
        with self.path.open("rb") as file:
            for key in sorted(set(keys)):
                for offset in self.offsets.get(key, ()):
                    file.seek(offset)
                    found.setdefault(key, []).append(json.loads(file.readline()))
        return found
