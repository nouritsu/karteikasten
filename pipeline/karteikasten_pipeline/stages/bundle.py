"""Stage 70: the deck bundle the app loads.

data/dist/deck/<version>/ holds manifest.json, deck.sqlite (canonical),
words.json (what the app reads), attribution.json (every source and every media
item and sentence credit), coverage.md and media/. The version is the snapshot's
date plus a short hash of every input, so the same inputs give the same
directory, byte for byte: rows are written in a fixed order, JSON with sorted
keys, and no file records when it was built.
"""

import hashlib
import json
import shutil
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE word (
    id TEXT PRIMARY KEY, rank INTEGER NOT NULL, lemma TEXT NOT NULL, pos TEXT NOT NULL,
    gender TEXT, article TEXT, token_share REAL NOT NULL, coverage_cum REAL NOT NULL,
    ipa TEXT, syllables TEXT, stress_syllable INTEGER, cognate_en TEXT,
    flags TEXT NOT NULL, key_forms TEXT NOT NULL, tables TEXT NOT NULL,
    gloss_en TEXT NOT NULL, gloss_de TEXT NOT NULL, audio_id TEXT REFERENCES media(id),
    provenance TEXT NOT NULL
);
CREATE TABLE sentence (
    id TEXT NOT NULL, word_id TEXT NOT NULL REFERENCES word(id), position INTEGER NOT NULL,
    de TEXT NOT NULL, en TEXT, source TEXT NOT NULL, source_ref TEXT NOT NULL,
    author TEXT NOT NULL, license TEXT NOT NULL, en_author TEXT, en_license TEXT, native INTEGER NOT NULL,
    deck_token_ids TEXT NOT NULL, out_of_deck INTEGER NOT NULL, hl_start INTEGER NOT NULL, hl_end INTEGER NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (word_id, id)
);
CREATE TABLE media (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT NOT NULL, source TEXT NOT NULL, source_url TEXT,
    author TEXT NOT NULL, license TEXT NOT NULL, license_url TEXT, sha256 TEXT NOT NULL, duration_ms INTEGER NOT NULL
);
CREATE TABLE source (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT, license TEXT NOT NULL, retrieved_at TEXT, sha256 TEXT
);
"""


def deck_version(day: date, inputs: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:7]
    return f"{day:%Y.%m.%d}-{digest}"


def _json(data: Any, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)


def _dump(path: Path, data: Any, *, compact: bool = False) -> None:
    path.write_text(_json(data, compact=compact) + "\n", encoding="utf-8")


def write_sqlite(path: Path, words: list[dict[str, Any]], media: list[dict[str, Any]], sources: list[dict[str, Any]]) -> None:
    """deck.sqlite: the canonical deck. JSON columns hold lists and objects."""
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        con.executemany(
            "INSERT INTO source VALUES (?, ?, ?, ?, ?, ?)",
            [(s["id"], s["name"], s.get("url"), s["license"], s.get("retrieved_at"), s.get("sha256"))
             for s in sorted(sources, key=lambda s: s["id"])],
        )
        con.executemany(
            "INSERT INTO media VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(m["id"], m["kind"], m["path"], m["source"], m.get("source_url"), m["author"], m["license"],
              m.get("license_url"), m["sha256"], m["duration_ms"]) for m in sorted(media, key=lambda m: m["id"])],
        )
        for w in sorted(words, key=lambda w: w["rank"]):
            con.execute(
                "INSERT INTO word VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (w["id"], w["rank"], w["lemma"], w["pos"], w["gender"], w["article"], w["token_share"],
                 w["coverage_cum"], w["ipa"], _json(w["syllables"], compact=True) if w["syllables"] else None,
                 w["stress_syllable"], w["cognate_en"], _json(w["flags"], compact=True),
                 _json(w["key_forms"], compact=True), _json(w["tables"], compact=True),
                 _json(w["gloss_en"], compact=True), _json(w["gloss_de"], compact=True),
                 w["audio"]["id"] if w["audio"] else None, _json(w["provenance"], compact=True)),
            )
            for position, s in enumerate(w["sentences"]):
                con.execute(
                    "INSERT INTO sentence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (s["id"], w["id"], position, s["de"], s["en"], s["source"], s["source_ref"], s["author"],
                     s["license"], s["en_author"], s["en_license"], int(s["native"]),
                     _json(s["deck_token_ids"], compact=True), s["out_of_deck"], s["hl"][0], s["hl"][1], s["score"]),
                )
        con.commit()
        con.execute("VACUUM")
    finally:
        con.close()


def write(
    dest: Path,
    *,
    manifest: dict[str, Any],
    words: list[dict[str, Any]],
    media: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    attribution: dict[str, Any],
    coverage: str,
    media_dir: Path,
) -> Path:
    """Write the bundle into `dest` (replacing it) and return it. `media_dir` holds
    the processed files that `media` rows name by path (media/audio/<sha1>.mp3)."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    _dump(dest / "manifest.json", {"schema_version": SCHEMA_VERSION, **manifest})
    _dump(dest / "words.json", sorted(words, key=lambda w: w["rank"]), compact=True)
    _dump(dest / "attribution.json", attribution)
    (dest / "coverage.md").write_text(coverage, encoding="utf-8")
    write_sqlite(dest / "deck.sqlite", words, media, sources)
    for relative in sorted({m["path"] for m in media}):
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(media_dir / Path(relative).relative_to("media"), target)
    return dest


def tree_digest(directory: Path) -> str:
    """sha256 over every file's relative path and bytes: equal for byte-identical bundles."""
    sha = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        sha.update(path.relative_to(directory).as_posix().encode())
        sha.update(hashlib.sha256(path.read_bytes()).digest())
    return sha.hexdigest()
