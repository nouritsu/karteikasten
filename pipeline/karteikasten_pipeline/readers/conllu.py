"""A small CoNLL-U reader (nixpkgs has no Python package for it).

Yields one sentence at a time as its syntactic words. Each word knows the surface
token it belongs to, so a contraction such as "zum" (zu + dem) can be counted
once, the way it appears in running text. Empty nodes are skipped.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Word:
    id: int
    form: str
    lemma: str
    upos: str
    xpos: str  # language-specific tag; STTS in the German treebanks
    head: int
    deprel: str
    token: str  # surface token: the word's own form, or the contraction it is part of
    token_start: bool  # first word of its token (always true outside contractions)


def read(path: Path) -> Iterator[list[Word]]:
    sentence: list[Word] = []
    contraction: tuple[int, int, str] | None = None  # first id, last id, surface form
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.rstrip("\n")
            if not line:
                if sentence:
                    yield sentence
                sentence, contraction = [], None
                continue
            if line.startswith("#"):
                continue
            cols = line.split("\t")
            if "." in cols[0]:
                continue
            if "-" in cols[0]:
                first, last = cols[0].split("-")
                contraction = (int(first), int(last), cols[1])
                continue
            word_id = int(cols[0])
            inside = contraction is not None and contraction[0] <= word_id <= contraction[1]
            sentence.append(
                Word(
                    id=word_id,
                    form=cols[1],
                    lemma=cols[2],
                    upos=cols[3],
                    xpos=cols[4],
                    head=int(cols[6]) if cols[6].isdigit() else 0,
                    deprel=cols[7],
                    token=contraction[2] if inside else cols[1],
                    token_start=not inside or word_id == contraction[0],
                )
            )
    if sentence:
        yield sentence
