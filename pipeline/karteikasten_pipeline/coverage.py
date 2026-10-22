"""Coverage per field and the Phase 3 targets (confirmed 2026-10-22, reports/phase1-coverage.md).

Computed from the deck's own word records, so the report always describes the
bundle it ships with. The targets apply after curation: a gap that only a human
can close (a gloss, a recording) is listed by word so it can be fixed.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

Word = dict[str, Any]
STRENGTH = frozenset({"strong", "weak", "mixed", "modal"})
VERB_CORE = ("er", "praeteritum", "partizip2", "auxiliary")


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    applies: Callable[[Word], bool]
    has: Callable[[Word], bool]
    target: float | None = None  # share of the top n that must have it


def _pos(*names: str) -> Callable[[Word], bool]:
    return lambda w: w["pos"] in names


def _all(_: Word) -> bool:
    return True


def _full_noun(w: Word) -> bool:
    """Nouns that need gender, plural and genitive: not abbreviations (D51)."""
    return w["pos"] == "noun" and "abbreviation" not in w["flags"]


def _noun_plural(w: Word) -> bool:
    return bool(w["key_forms"].get("plural")) or bool({"plural_only", "singular_only"} & set(w["flags"]))


def _noun_genitive(w: Word) -> bool:
    return bool(w["key_forms"].get("genitive")) or "plural_only" in w["flags"]


FIELDS: tuple[Field, ...] = (
    Field("gloss_en", "English gloss", _all, lambda w: bool(w["gloss_en"]), 1.0),
    Field("ipa", "IPA", _all, lambda w: bool(w["ipa"]), 1.0),
    Field("audio", "Audio", _all, lambda w: w["audio"] is not None, 1.0),
    Field("sentence", "At least 1 sentence", _all, lambda w: len(w["sentences"]) >= 1, 1.0),
    Field("gloss_de", "German definition", _all, lambda w: bool(w["gloss_de"]), 0.95),
    Field("noun_gender", "Noun gender or plural only", _full_noun, lambda w: bool(w["article"]), 1.0),
    Field("noun_plural", "Noun plural (or flag)", _full_noun, _noun_plural, 1.0),
    Field("noun_genitive", "Noun genitive (or plural only)", _full_noun, _noun_genitive, 1.0),
    Field("verb_core", "Verb er-form, Präteritum, Partizip II, auxiliary", _pos("verb"),
          lambda w: all(w["key_forms"].get(k) for k in VERB_CORE), 1.0),
    Field("verb_strength", "Verb class (strong, weak, mixed, modal)", _pos("verb"),
          lambda w: bool(STRENGTH & set(w["flags"])), 0.98),
    Field("prep_case", "Preposition case", _pos("prep", "postp"), lambda w: bool(w["key_forms"].get("case")), 1.0),
    Field("conj_type", "Conjunction type", _pos("conj"), lambda w: bool(w["key_forms"].get("conjunction")), 1.0),
    Field("stress", "Stress highlight", _all, lambda w: w["stress_syllable"] is not None, 0.93),
    Field("five_sentences", "5 sentences", _all, lambda w: len(w["sentences"]) >= 5, 0.99),
    Field("syllables", "Syllables", _all, lambda w: bool(w["syllables"])),
    Field("noun_table", "Noun table with articles", _pos("noun"), lambda w: bool(w["tables"].get("declension"))),
    Field("verb_tables", "Verb tables", _pos("verb"), lambda w: bool(w["tables"].get("present"))),
    Field("adj_comparison", "Adjective comparison", _pos("adj"), lambda w: bool(w["key_forms"].get("comparative"))),
    Field("case_table", "Article, determiner, pronoun table", _pos("article", "det", "pron"),
          lambda w: bool(w["tables"].get("cases"))),
    Field("ordinal", "Numeral ordinal", _pos("num"), lambda w: bool(w["key_forms"].get("ordinal"))),
    Field("cognate", "Cognate hint", _all, lambda w: bool(w["cognate_en"])),
    Field("native_best", "Best sentence native with English", _all,
          lambda w: bool(w["sentences"]) and w["sentences"][0]["native"] and bool(w["sentences"][0]["en"])),
)


def share(words: Sequence[Word], field: Field) -> tuple[float, int]:
    """(share that has the field, number it applies to)."""
    applicable = [w for w in words if field.applies(w)]
    if not applicable:
        return 1.0, 0
    return sum(1 for w in applicable if field.has(w)) / len(applicable), len(applicable)


def gaps(words: Sequence[Word], field: Field) -> list[str]:
    return [w["id"] for w in words if field.applies(w) and not field.has(w)]


def summary(words: Sequence[Word]) -> dict[str, Any]:
    """Shares over the whole deck, for manifest.json."""
    return {f.key: round(share(words, f)[0], 4) for f in FIELDS}


def met(words: Sequence[Word], field: Field) -> bool | None:
    if field.target is None:
        return None
    value, _ = share(words, field)
    return value >= field.target - 1e-9


def _percent(value: float, count: int) -> str:
    return "n/a" if count == 0 else f"{value * 100:.1f}%"


def render(words: Sequence[Word], *, deck_version: str, profile: str, extra: dict[str, Any]) -> str:
    """coverage.md: per-field shares at the top 100, 500 and n, the targets, and gaps."""
    words = sorted(words, key=lambda w: w["rank"])
    n = len(words)
    cuts = [c for c in (100, 500) if c < n] + [n]
    lines = [
        f"# Coverage: deck {deck_version}",
        "",
        f"Profile `{profile}`, {n:,} words. Targets apply to the top {n:,} after curation (confirmed 2026-10-22).",
        "",
        "| Field | " + " | ".join(f"Top {c:,}" for c in cuts) + " | Target | Met |",
        "| --- | " + " | ".join("---" for _ in cuts) + " | --- | --- |",
    ]
    for field in FIELDS:
        cells = []
        for cut in cuts:
            value, count = share(words[:cut], field)
            cells.append(_percent(value, count) + ("" if field.applies is _all else f" of {count:,}"))
        target = "" if field.target is None else f"{'≥ ' if field.target < 1 else ''}{field.target * 100:g}%"
        ok = met(words, field)
        lines.append(f"| {field.label} | " + " | ".join(cells) + f" | {target} | {'' if ok is None else ('yes' if ok else 'no')} |")
    lines += ["", "## Gaps", ""]
    any_gap = False
    for field in FIELDS:
        if field.target is None:
            continue
        missing = gaps(words, field)
        if missing:
            any_gap = True
            shown = ", ".join(f"`{id_}`" for id_ in missing[:60])
            more = f" and {len(missing) - 60} more" if len(missing) > 60 else ""
            lines.append(f"- {field.label} ({len(missing)}): {shown}{more}")
    if not any_gap:
        lines.append("None.")
    if extra:
        lines += ["", "## Notes", ""]
        for key, value in extra.items():
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"
