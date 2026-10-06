"""FrequencyWords lists: one "word count" pair per line, case-folded (docs/sources/frequencywords.md)."""

from pathlib import Path


def read(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            word, _, count = line.rstrip("\n").rpartition(" ")
            if word:
                counts[word] = counts.get(word, 0) + int(count)
    return counts
