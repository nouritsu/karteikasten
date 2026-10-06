"""Tatoeba weekly exports (per-language TSV, bzip2), field notes in docs/sources/tatoeba.md.

Files are opened with newline="" because some fields contain a stray carriage
return that universal-newline mode would split on.
"""

import bz2
import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

LICENCE = "CC BY 2.0 FR"
NULL = "\\N"


@dataclass(frozen=True, slots=True)
class Sentence:
    id: int
    lang: str
    text: str
    author: str | None
    licence: str


def _rows(path: Path) -> Iterator[list[str]]:
    with bz2.open(path, "rt", encoding="utf-8", newline="") as file:
        yield from csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)


def cc0_ids(path: Path) -> set[int]:
    return {int(row[0]) for row in _rows(path) if row}


def sentences(path: Path, cc0: set[int]) -> Iterator[Sentence]:
    """sentences_detailed: id, lang, text, username, date added, date modified."""
    for row in _rows(path):
        if len(row) < 4:
            continue
        sentence_id = int(row[0])
        yield Sentence(
            id=sentence_id,
            lang=row[1],
            text=row[2],
            author=None if row[3] == NULL else row[3],
            licence="CC0 1.0" if sentence_id in cc0 else LICENCE,
        )


def links(path: Path) -> Iterator[tuple[int, int]]:
    for row in _rows(path):
        if len(row) >= 2:
            yield int(row[0]), int(row[1])


def tags(path: Path) -> Iterator[tuple[int, str]]:
    for row in _rows(path):
        if len(row) >= 2:
            yield int(row[0]), row[1]


def skill_levels(path: Path) -> dict[str, int]:
    """user_languages for one language: lang, level (0-5, 5 = native), username, details."""
    levels: dict[str, int] = {}
    for row in _rows(path):
        if len(row) >= 3 and row[1].isdigit() and row[2] != NULL:
            levels[row[2]] = int(row[1])
    return levels
