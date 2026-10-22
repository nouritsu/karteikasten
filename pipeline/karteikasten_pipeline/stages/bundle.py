"""Stage 70: the deck bundle the app loads.

data/dist/deck/<version>/ holds manifest.json, words.json (what the app reads),
attribution.json (every source and every media item and sentence credit) and
media/. The version is the build date plus a short hash of the inputs, so the
same inputs give the same directory, byte for byte.
"""

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def deck_version(day: date, inputs: dict[str, str]) -> str:
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:7]
    return f"{day:%Y.%m.%d}-{digest}"


def _dump(path: Path, data: Any, *, compact: bool = False) -> None:
    if compact:
        text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    else:
        text = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def write(
    dest: Path,
    *,
    manifest: dict[str, Any],
    words: list[dict[str, Any]],
    attribution: dict[str, Any],
    media: Path,
) -> Path:
    """Write the bundle into `dest` (replacing it) and return it."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    _dump(dest / "manifest.json", {"schema_version": SCHEMA_VERSION, **manifest})
    _dump(dest / "words.json", sorted(words, key=lambda w: w["rank"]), compact=True)
    _dump(dest / "attribution.json", attribution)
    used = {word["audio"]["path"] for word in words if word.get("audio")}
    for relative in sorted(used):
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(media / Path(relative).relative_to("media"), target)
    return dest
