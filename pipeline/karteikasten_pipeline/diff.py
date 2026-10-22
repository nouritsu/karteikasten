"""Build-to-build diff: what changed between two decks, as Markdown (`report --diff`).

Read from each deck's own words.json and manifest.json, so any two decks in
data/dist/deck can be compared. Sections: which inputs changed, words entering
and leaving the deck, rank moves, card changes per field, coverage, and the
issues fixed and new (the automated checks of curation.py, run on both decks).
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from karteikasten_pipeline import coverage, curation
from karteikasten_pipeline.stages.enrich import stressed_syllable

Word = dict[str, Any]
EXAMPLES = 10  # changes listed per section; the rest are counted
MOVES = 15


@dataclass(frozen=True)
class Deck:
    version: str
    manifest: dict[str, Any]
    words: dict[str, Word]  # id -> record

    @classmethod
    def load(cls, directory: Path) -> "Deck":
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        words = json.loads((directory / "words.json").read_text(encoding="utf-8"))
        return cls(manifest["deck_version"], manifest, {w["id"]: w for w in words})


def previous(decks: Path, version: str) -> str | None:
    """The deck built most recently before `version`, by manifest time; fixture and
    spike decks from Phase 1 are skipped."""
    built = sorted(
        (m.stat().st_mtime, m.parent.name)
        for m in decks.glob("*/manifest.json")
        if m.parent.name != version and not m.parent.name.endswith(("-fixtures", "-spike"))
    )
    current = decks / version / "manifest.json"
    older = [name for mtime, name in built if not current.exists() or mtime <= current.stat().st_mtime]
    return older[-1] if older else None


def _gloss(w: Word, field: str) -> str:
    return "; ".join(g["text"] for g in w[field]) or "—"


def _forms(w: Word) -> str:
    return json.dumps(w["key_forms"], ensure_ascii=False, sort_keys=True)


def _audio(w: Word) -> str:
    a = w["audio"]
    return "—" if a is None else (a.get("source_url") or a["source"]).rsplit("File:", 1)[-1]


def _stress(w: Word) -> str:
    syllables = w["syllables"] or []
    return "·".join(s.upper() if i == w["stress_syllable"] else s for i, s in enumerate(syllables)) or "—"


# field label, value shown per word
CARD_FIELDS: tuple[tuple[str, Callable[[Word], str]], ...] = (
    ("English gloss", lambda w: _gloss(w, "gloss_en")),
    ("German definition", lambda w: _gloss(w, "gloss_de")),
    ("IPA", lambda w: w["ipa"] or "—"),
    ("Article", lambda w: w["article"] or "—"),
    ("Flags", lambda w: ", ".join(sorted(w["flags"])) or "—"),
    ("Key forms", _forms),
    ("Syllables and stress", _stress),
    ("Cognate hint", lambda w: w["cognate_en"] or "—"),
    ("Audio", _audio),
)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _name(w: Word) -> str:
    return f"*{w['lemma']}* ({w['pos']}, #{w['rank']})"


def _more(count: int) -> list[str]:
    return [f"- and {count - EXAMPLES:,} more"] if count > EXAMPLES else []


def _with_notes(w: Word) -> Word:
    """words.json leaves out stage 40's notes; the syllable/stress one follows from
    the IPA and the hyphenation, as in enrich.build_card."""
    if "issues" in w or not (w["ipa"] and w["syllables"]):
        return w
    _, count = stressed_syllable(w["ipa"])
    if count == len(w["syllables"]):
        return w
    return {**w, "issues": [f"syllables: {len(w['syllables'])} in hyphenation, {count} in IPA"]}


def _issues(words: Iterable[Word]) -> set[tuple[str, str, str]]:
    words = [_with_notes(w) for w in words]
    found = curation.issues(words, curation.duration_outliers(words))
    return {(i.severity, i.word_id, i.code) for i in found}


def render(old: Deck, new: Deck) -> str:
    lines = [f"# Diff: deck {old.version} → {new.version}", ""]

    changed = [k for k in sorted(set(old.manifest["inputs"]) | set(new.manifest["inputs"]))
               if old.manifest["inputs"].get(k) != new.manifest["inputs"].get(k)]
    lines += [f"Inputs changed: {', '.join(changed) or 'none'}. Words: {len(old.words):,} → {len(new.words):,}.", ""]

    entered = sorted((new.words[i] for i in set(new.words) - set(old.words)), key=lambda w: w["rank"])
    left = sorted((old.words[i] for i in set(old.words) - set(new.words)), key=lambda w: w["rank"])
    lines += ["## Words", ""]
    lines += [f"- Entered ({len(entered):,}): " + (", ".join(_name(w) for w in entered[:EXAMPLES]) or "none")]
    lines += [f"- Left ({len(left):,}): " + (", ".join(_name(w) for w in left[:EXAMPLES]) or "none")]
    both = sorted(set(old.words) & set(new.words), key=lambda i: new.words[i]["rank"])
    moves = sorted(((abs(new.words[i]["rank"] - old.words[i]["rank"]), i) for i in both
                    if new.words[i]["rank"] != old.words[i]["rank"]), key=lambda m: (-m[0], new.words[m[1]]["rank"]))
    lines += [f"- Rank changed: {len(moves):,}", ""]
    if moves:
        lines += ["| Word | Old rank | New rank |", "| --- | --- | --- |"]
        lines += [f"| *{new.words[i]['lemma']}* ({new.words[i]['pos']}) | {old.words[i]['rank']} | "
                  f"{new.words[i]['rank']} |" for _, i in moves[:MOVES]]
        lines += [""]

    lines += ["## Cards", ""]
    any_card = False
    for label, value in CARD_FIELDS:
        diffs = [(new.words[i], value(old.words[i]), value(new.words[i])) for i in both
                 if value(old.words[i]) != value(new.words[i])]
        if not diffs:
            continue
        any_card = True
        lines += [f"### {label} ({len(diffs):,})", "", "| Word | Old | New |", "| --- | --- | --- |"]
        lines += [f"| {_name(w)} | {_cell(a)} | {_cell(b)} |" for w, a, b in diffs[:EXAMPLES]]
        lines += [""] + ([f"And {len(diffs) - EXAMPLES:,} more.", ""] if len(diffs) > EXAMPLES else [])
    sentence_diffs = []
    for i in both:
        before = [s["id"] for s in old.words[i]["sentences"]]
        after = [s["id"] for s in new.words[i]["sentences"]]
        if before != after:
            sentence_diffs.append((new.words[i], len(set(after) - set(before)), len(set(before) - set(after))))
    if sentence_diffs:
        any_card = True
        lines += [f"### Sentences ({len(sentence_diffs):,})", ""]
        lines += [f"- {_name(w)}: {added} new, {dropped} dropped" + ("" if added or dropped else ", reordered")
                  for w, added, dropped in sentence_diffs[:EXAMPLES]]
        lines += _more(len(sentence_diffs)) + [""]
    if not any_card:
        lines += ["No card changed.", ""]

    lines += ["## Coverage (top {:,})".format(len(new.words)), ""]
    rows = []
    for field in coverage.FIELDS:
        a, _ = coverage.share(list(old.words.values()), field)
        b, _ = coverage.share(list(new.words.values()), field)
        if round(a, 4) != round(b, 4):
            rows.append(f"| {field.label} | {a:.1%} | {b:.1%} | {(b - a) * 100:+.1f} |")
    lines += (["| Field | Old | New | Points |", "| --- | --- | --- | --- |", *rows] if rows else ["No change."]) + [""]

    before, after = _issues(old.words.values()), _issues(new.words.values())
    lines += ["## Issues", ""]
    for severity in ("blocking", "warning"):
        fixed = sorted((i for i in before - after if i[0] == severity), key=lambda i: (i[2], i[1]))
        added = sorted((i for i in after - before if i[0] == severity), key=lambda i: (i[2], i[1]))
        total = sum(1 for i in after if i[0] == severity)
        lines += [f"- {severity.capitalize()}: {total:,} now; {len(fixed):,} fixed, {len(added):,} new"]
        for verb, items in (("fixed", fixed), ("new", added)):
            if items:
                lines += [f"  - {verb}: " + ", ".join(f"`{word}` {code}" for _, word, code in items[:EXAMPLES])
                          + (f" and {len(items) - EXAMPLES:,} more" if len(items) > EXAMPLES else "")]
    return "\n".join(lines).rstrip() + "\n"
