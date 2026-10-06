"""Human curation in overrides/, re-applied on every build.

An override that no longer matches anything fails the build, so a stale entry
never silently stops doing its job.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WordOverrides:
    exclude: dict[str, str]  # lemma id -> reason


def load_words(path: Path) -> WordOverrides:
    data = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return WordOverrides(exclude=dict(data.get("exclude", {})))


def unmatched(overrides: WordOverrides, known_ids: set[str]) -> list[str]:
    return sorted(id_ for id_ in overrides.exclude if id_ not in known_ids)
