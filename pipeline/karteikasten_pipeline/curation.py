"""data/work/curation.sqlite: what the curation tool (Phase 4) works from.

Every audio candidate and the best sentence candidates per word, which of them
the build picked, and QA issues with a severity (spec: Curation tool). The tool
reads this database and writes overrides/; the next build applies them.
"""

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE word (id TEXT PRIMARY KEY, rank INTEGER NOT NULL, lemma TEXT NOT NULL, pos TEXT NOT NULL);
CREATE TABLE audio_candidate (
    word_id TEXT NOT NULL, file TEXT NOT NULL, author TEXT, license TEXT, region TEXT,
    usable INTEGER NOT NULL, picked INTEGER NOT NULL, PRIMARY KEY (word_id, file)
);
CREATE TABLE sentence_candidate (
    word_id TEXT NOT NULL, sentence_id TEXT NOT NULL, de TEXT NOT NULL, en TEXT, author TEXT, license TEXT,
    native INTEGER NOT NULL, score REAL NOT NULL, picked INTEGER NOT NULL, PRIMARY KEY (word_id, sentence_id)
);
CREATE TABLE issue (word_id TEXT NOT NULL, severity TEXT NOT NULL, code TEXT NOT NULL, detail TEXT NOT NULL);
"""


@dataclass(frozen=True)
class Issue:
    word_id: str
    severity: str  # blocking | warning
    code: str
    detail: str


def issues(words: Iterable[dict[str, Any]], duration_outliers: set[str]) -> list[Issue]:
    """The automated checks of the spec's curation table, per word."""
    found: list[Issue] = []
    for w in words:
        id_, k, flags = w["id"], w["key_forms"], set(w["flags"])

        def add(severity: str, code: str, detail: str) -> None:
            found.append(Issue(id_, severity, code, detail))

        if w["pos"] == "noun" and not w["article"]:
            add("blocking", "noun-gender", "noun without gender")
        if w["pos"] == "noun" and not (k.get("plural") or {"plural_only", "singular_only"} & flags):
            add("blocking", "noun-plural", "noun without plural or plural/singular-only flag")
        if w["pos"] == "verb" and not (k.get("partizip2") and k.get("auxiliary")):
            add("blocking", "verb-perfect", "verb without Partizip II or auxiliary")
        if not w["gloss_en"]:
            add("blocking", "gloss-en", "no English gloss")
        items = ([w["audio"]] if w["audio"] else []) + w["sentences"]
        for item in items:
            if not item.get("author") or not item.get("license"):
                add("blocking", "credit", f"{item.get('id') or item.get('path')} without licence or author")
        if not w["audio"]:
            add("warning", "no-audio", "no audio")
        if not w["sentences"]:
            add("warning", "no-sentence", "no sentence")
        for note in w.get("issues", []):
            if note.startswith("syllables:"):
                add("warning", "syllable-stress", note)
        if id_ in duration_outliers:
            add("warning", "audio-duration", f"audio {w['audio']['duration_ms']} ms is an outlier")
    return found


def duration_outliers(words: Iterable[dict[str, Any]]) -> set[str]:
    """Words whose audio is under a quarter or over four times the median length."""
    timed = [(w["id"], w["audio"]["duration_ms"]) for w in words if w["audio"]]
    if not timed:
        return set()
    durations = sorted(d for _, d in timed)
    median = durations[len(durations) // 2]
    return {id_ for id_, d in timed if d < median / 4 or d > median * 4}


def write(
    path: Path,
    words: list[dict[str, Any]],
    audio_candidates: dict[str, list[dict[str, Any]]],
    sentence_candidates: dict[str, list[dict[str, Any]]],
    found: list[Issue],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    try:
        con.executescript(SCHEMA)
        con.executemany("INSERT INTO word VALUES (?, ?, ?, ?)", [(w["id"], w["rank"], w["lemma"], w["pos"]) for w in words])
        con.executemany(
            "INSERT INTO audio_candidate VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(id_, c["file"], c["author"], c["license"], c["region"], int(c["usable"]), int(c["picked"]))
             for id_, cands in sorted(audio_candidates.items()) for c in cands],
        )
        con.executemany(
            "INSERT OR IGNORE INTO sentence_candidate VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(id_, c["id"], c["de"], c["en"], c["author"], c["license"], int(c["native"]), c["score"], int(c["picked"]))
             for id_, cands in sorted(sentence_candidates.items()) for c in cands],
        )
        con.executemany(
            "INSERT INTO issue VALUES (?, ?, ?, ?)", [(i.word_id, i.severity, i.code, i.detail) for i in found]
        )
        con.commit()
    finally:
        con.close()
    tmp.replace(path)


def as_json(found: list[Issue]) -> str:
    return json.dumps([i.__dict__ for i in found], ensure_ascii=False, indent=1)
