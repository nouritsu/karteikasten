"""Human curation in overrides/, re-applied on every build.

An override that no longer matches anything fails the build, so a stale entry
never silently stops doing its job. Everything here carries provenance `manual`.

- words.toml: [exclude] ids with a reason; [merge] an id into the card of
  another (its frequency and senses join that card); [gloss_en] / [gloss_de]
  glosses that replace the extracted ones; [no_cognate] cognate hints dropped;
  [audio] the Commons file a word uses instead of the build's pick.
- closed_classes.toml: [preposition] cases governed (first the main one;
  acc + dat is two-way) and optionally contractions; [conjunction] coordinating
  or subordinating.
- sentences.toml: [pin] sentence ids shown first for a word, in order;
  [ban] sentence ids a word never shows.
- audio/: own recordings named by word id with "#" as "_" (Hand_noun_1.flac).
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CASES = frozenset({"nom", "acc", "dat", "gen"})
CONJUNCTION_TYPES = frozenset({"coordinating", "subordinating"})
RECORDING_SUFFIXES = frozenset({".flac", ".wav", ".ogg", ".opus", ".mp3"})


class OverrideError(Exception):
    """An override that is malformed or no longer matches anything."""


@dataclass(frozen=True)
class WordOverrides:
    exclude: dict[str, str] = field(default_factory=dict)  # id -> reason
    merge: dict[str, str] = field(default_factory=dict)  # absorbed id -> id of the card it joins
    gloss_en: dict[str, list[str]] = field(default_factory=dict)
    gloss_de: dict[str, list[str]] = field(default_factory=dict)
    no_cognate: dict[str, str] = field(default_factory=dict)  # id -> reason
    audio: dict[str, str] = field(default_factory=dict)  # id -> Commons file name, one of its candidates


@dataclass(frozen=True)
class ClosedClasses:
    prepositions: dict[str, list[str]] = field(default_factory=dict)  # id -> cases, main one first
    contractions: dict[str, list[str]] = field(default_factory=dict)  # id -> contractions, if set by hand
    conjunctions: dict[str, str] = field(default_factory=dict)  # id -> coordinating | subordinating


@dataclass(frozen=True)
class SentenceOverrides:
    pin: dict[str, list[str]] = field(default_factory=dict)  # word id -> sentence ids
    ban: dict[str, list[str]] = field(default_factory=dict)  # word id -> sentence ids


@dataclass(frozen=True)
class Overrides:
    words: WordOverrides = field(default_factory=WordOverrides)
    closed: ClosedClasses = field(default_factory=ClosedClasses)
    sentences: SentenceOverrides = field(default_factory=SentenceOverrides)
    recordings: dict[str, Path] = field(default_factory=dict)  # word id -> own recording

    def ids(self) -> set[str]:
        """Every word id an override names; each must exist in the lexicon."""
        w, c, s = self.words, self.closed, self.sentences
        return (
            set(w.exclude) | set(w.merge) | set(w.merge.values()) | set(w.gloss_en) | set(w.gloss_de)
            | set(w.no_cognate) | set(w.audio) | set(c.prepositions) | set(c.contractions) | set(c.conjunctions)
            | set(s.pin) | set(s.ban) | set(self.recordings)
        )


def _toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise OverrideError(f"{path}: {error}") from error


def _strings(path: Path, table: str, data: dict) -> dict[str, list[str]]:
    result = {}
    for id_, value in data.get(table, {}).items():
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            raise OverrideError(f"{path}: [{table}] {id_!r} must be a list of strings")
        result[id_] = list(value)
    return result


def load_words(path: Path) -> WordOverrides:
    data = _toml(path)
    merge = dict(data.get("merge", {}))
    for absorbed, target in merge.items():
        if target in merge:
            raise OverrideError(f"{path}: [merge] {absorbed!r} joins {target!r}, which itself joins another card")
    audio = dict(data.get("audio", {}))
    for id_, file in audio.items():
        if not isinstance(file, str) or not file:
            raise OverrideError(f"{path}: [audio] {id_!r} must be a Commons file name")
    return WordOverrides(
        exclude=dict(data.get("exclude", {})),
        merge=merge,
        gloss_en=_strings(path, "gloss_en", data),
        gloss_de=_strings(path, "gloss_de", data),
        no_cognate=dict(data.get("no_cognate", {})),
        audio=audio,
    )


def load_closed_classes(path: Path) -> ClosedClasses:
    data = _toml(path)
    prepositions, contractions = {}, {}
    for id_, entry in data.get("preposition", {}).items():
        cases = entry.get("cases", [])
        if not cases or not set(cases) <= CASES or len(set(cases)) != len(cases):
            raise OverrideError(f"{path}: [preposition] {id_!r}: cases must be distinct, from {sorted(CASES)}")
        prepositions[id_] = list(cases)
        if "contractions" in entry:
            contractions[id_] = list(entry["contractions"])
    conjunctions = {}
    for id_, kind in data.get("conjunction", {}).items():
        if kind not in CONJUNCTION_TYPES:
            raise OverrideError(f"{path}: [conjunction] {id_!r}: {kind!r} is not one of {sorted(CONJUNCTION_TYPES)}")
        conjunctions[id_] = kind
    return ClosedClasses(prepositions=prepositions, contractions=contractions, conjunctions=conjunctions)


def load_sentences(path: Path) -> SentenceOverrides:
    data = _toml(path)
    return SentenceOverrides(pin=_strings(path, "pin", data), ban=_strings(path, "ban", data))


def recording_id(path: Path) -> str:
    """Hand_noun_1.flac -> Hand#noun#1 (the lemma may itself contain "_")."""
    lemma, pos, etym = path.stem.rsplit("_", 2)
    return f"{lemma}#{pos}#{etym}"


def load_recordings(directory: Path) -> dict[str, Path]:
    recordings = {}
    for path in sorted(directory.glob("*")) if directory.is_dir() else []:
        if path.suffix.lower() not in RECORDING_SUFFIXES:
            continue
        if path.stem.count("_") < 2:
            raise OverrideError(f"{path}: name it by word id with '#' as '_', like Hand_noun_1{path.suffix}")
        id_ = recording_id(path)
        if id_ in recordings:
            raise OverrideError(f"{path}: a second recording for {id_}")
        recordings[id_] = path
    return recordings


def load(directory: Path) -> Overrides:
    return Overrides(
        words=load_words(directory / "words.toml"),
        closed=load_closed_classes(directory / "closed_classes.toml"),
        sentences=load_sentences(directory / "sentences.toml"),
        recordings=load_recordings(directory / "audio"),
    )


def unmatched(overrides: Overrides, known_ids: set[str]) -> list[str]:
    """Ids named by an override that the lexicon does not know."""
    return sorted(overrides.ids() - known_ids)
