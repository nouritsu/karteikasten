"""Draft overrides/closed_classes.toml from what both Wiktionary editions say.

After a build, data/work/closed-classes.json holds the evidence for every
preposition and conjunction in the deck. This writes one entry per word that the
file does not have yet, each with a comment quoting the evidence; entries where
the editions disagree are marked CHECK. Nothing here is decided by the program
beyond ordering what Wiktionary says: you check the file by hand (spec: closed
classes are hand-checked against Wiktionary).

From the dev shell, inside the checkout:  python -m karteikasten_pipeline.draft
With an existing file, the new entries are printed instead, to paste in.
"""

import json
import sys
import tomllib
from pathlib import Path

from karteikasten_pipeline.paths import find_root

CASE_NAMES = {"nom": "nominative", "acc": "accusative", "dat": "dative", "gen": "genitive"}
HEADER = """\
# Closed classes, hand-checked against Wiktionary and merged in stage 40; they win
# over what the build extracts (provenance `manual`).
#
# [preposition] "id" = { cases = [...] }: the cases governed, the main one first
#   (nom, acc, dat, gen); acc and dat together make a two-way preposition.
#   Optional `contractions = [...]` replaces the contractions found in Wiktionary.
# [conjunction] "id" = "coordinating" | "subordinating"
#
# Drafted by `python -m karteikasten_pipeline.draft` from both editions: the comment
# above each entry is what they say. CHECK marks entries where they disagree.
"""


def _list(cases: list[str]) -> str:
    return ", ".join(cases) if cases else "nothing"


def _check(agree: bool, en: list, de: list) -> str:
    if not agree:
        return "CHECK: the editions disagree. "
    if not en or not de:
        return f"Only the {'German' if de else 'English'} edition says. " if en or de else ""
    return ""


def preposition_entry(id_: str, ev: dict) -> str:
    word = id_.split("#")[0]
    check = _check(ev["agree"], ev["en"], ev["de_main"] + ev["de_secondary"])
    lines = [f"# {word} (rank {ev['rank']}). {check}en categories: {_list(ev['en'])}; "
             f"de tags: {_list(ev['de_main'])}" + (f"; de, as colloquial/regional/old: {_list(ev['de_secondary'])}"
                                                   if ev["de_secondary"] else "") + "."]
    for note in ev["notes"]:
        lines.append(f"#   de note: {note}")
    if ev["cases"]:
        cases = ", ".join(f'"{c}"' for c in ev["cases"])
        lines.append(f'"{id_}" = {{ cases = [{cases}] }}')
    else:
        lines.append(f'# "{id_}" = {{ cases = [] }}  # Wiktionary names no case: fill in by hand')
    return "\n".join(lines)


def conjunction_entry(id_: str, ev: dict) -> str:
    word = id_.split("#")[0]
    check = _check(ev["agree"], ev["en"], ev["de"])
    line = f"# {word} (rank {ev['rank']}). {check}en categories: {_list(ev['en'])}; de: {_list(ev['de'])}."
    if ev["type"]:
        return f'{line}\n"{id_}" = "{ev["type"]}"'
    return f'{line}\n# "{id_}" = ""  # Wiktionary names no type: fill in by hand'


def draft(evidence: dict[str, dict], existing: dict) -> tuple[list[str], list[str]]:
    have_p, have_c = existing.get("preposition", {}), existing.get("conjunction", {})
    by_rank = sorted(evidence.items(), key=lambda kv: (kv[1]["rank"], kv[0]))
    preps = [preposition_entry(i, e) for i, e in by_rank if e["kind"] == "preposition" and i not in have_p]
    conjs = [conjunction_entry(i, e) for i, e in by_rank if e["kind"] == "conjunction" and i not in have_c]
    return preps, conjs


def main() -> int:
    root = find_root(Path.cwd())
    evidence = json.loads((root / "data/work/closed-classes.json").read_text(encoding="utf-8"))
    target = root / "overrides/closed_classes.toml"
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    existing = tomllib.loads(text)
    preps, conjs = draft(evidence, existing)
    if not preps and not conjs:
        print("closed_classes.toml already has every preposition and conjunction in the deck")
        return 0
    body = ""
    if preps:
        body += "[preposition]\n\n" + "\n\n".join(preps) + "\n"
    if conjs:
        body += ("\n" if body else "") + "[conjunction]\n\n" + "\n\n".join(conjs) + "\n"
    if existing:
        print(body)
        print(f"# {len(preps)} prepositions and {len(conjs)} conjunctions to add; paste them into {target}",
              file=sys.stderr)
        return 0
    target.write_text(HEADER + "\n" + body, encoding="utf-8")
    print(f"{target}: {len(preps)} prepositions and {len(conjs)} conjunctions drafted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
