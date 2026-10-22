# Phase 3 report: full pipeline (n = 2,000)

2026-10-22. Deck: `data/dist/deck/2026.10.22-eca993c/` (profile `personal`), built after your review below. Kaikki, Tatoeba and the corpora are the 2026-10-06 snapshot; the Commons audio was fetched today. Coverage per field: `reports/coverage.md`.

**Your review (2026-10-22):**

1. **Closed classes.** I checked the 10 open entries against both editions and you approved each; the comment above each entry in `overrides/closed_classes.toml` says "Checked 2026-10-22" with the evidence.
   - *vor*, *über*, *neben* stay two-way, *als* and *weil* subordinating, *sowie* coordinating: the editions only seemed to disagree because the draft read categories and missed the sense notes.
   - *ab* (dative), *pro* and *per* (accusative) lose their second case: acc and dat together make the card say "Wechselpräposition", which none of them is. *per* was not marked CHECK; it turned up in a pass over the rest of the file.
   - *lang* gets the accusative. Neither edition names its case; the evidence is that it is a colloquial *entlang*, which governs the accusative as a postposition.
   - *doch* as a conjunction is coordinating (English sense tag; the German edition's "Adversative Konjunktion").
2. **Abbreviations.** The 15 letters and abbreviations (*Dr.*, *TU*, *S.*, *St.*, *b.*, *S*, *N*, *A*, *I*, *M*, *O*, ...) stay in the deck as they are. They account for every remaining gap except one.
3. ***rauskommen*** has no recording linked from either edition, and stays without audio.
4. **D50** is accepted in the form below: a fourth class for the modal verbs, and *wissen* as mixed.

Optional: the multi-card words from Phase 1 (*sie* ×2, *ihr* ×3, *doch*, *aber*, *zu*, ...) can now be merged with `[merge]` in `words.toml`.

## Done criteria

| Criterion | Result |
| --- | --- |
| Two builds from the same snapshot are byte-identical | Yes, after a fix in stage 30 (below). Two `--fresh` builds in separate processes, with hash seeds 13 and 17, and a cached rebuild with seed 5 give the same 1,950 files (digest `1625cdb1…`). The fixture test does the same in pytest. |
| Every media item and sentence has source, author and licence | Yes. The build skips sentences and translations without a named author; the checks find no item without a credit. |
| pytest passes the tricky-word fixtures | Yes. 126 tests pass in the Nix check; 6 more check the real deck and pass here (the sandbox has no `data/`). |
| The coverage targets set in Phase 1 are met | 7 of 14. The other 7 miss only by the abbreviations you kept and *rauskommen*'s audio (next section). |

## Coverage against the targets (top 2,000)

| Field | Now | Target | What is missing |
| --- | --- | --- | --- |
| English gloss | 99.8% | 100% | *Dr.*, *TU*, *S.*, *St.*, *b.* |
| IPA | 99.9% | 100% | *Dr.*, *b.* |
| Audio | 99.9% | 100% | *Dr.*, *b.*, *rauskommen* |
| At least 1 sentence | 99.8% | 100% | *Dr.*, *S.*, *St.*, *b.* |
| German definition | 96.6% | ≥ 95% | met |
| Noun gender, plural or flag, genitive | 99.6–99.7% | 100% | *Dr.*, *TU*, *S.* |
| Verb core forms and auxiliary | 100% | 100% | met |
| Verb class | 100% | ≥ 98% | met (with D50) |
| Preposition case | 100% | 100% | met |
| Conjunction type | 100% | 100% | met |
| Stress highlight | 93.2% | ≥ 93% | met |
| 5 sentences | 99.5% | ≥ 99% | met |
| Cognate hint | 283 hints | 0 wrong | your judgement; see D49 |

Every gap left is an abbreviation you kept, plus *rauskommen*'s audio. The only blocking issue left in the top 500 is *Dr.* (no gender, no gloss), which Phase 4's done criterion counts.

## What the build does

`nix run .#build [--profile personal|public] [--fresh] [--offline]` runs stages 20–70. Times on this machine:
- First run: about an hour, almost all of it fetching 1,850 Commons recordings at the polite rate.
- Rebuild from cache: 42 s.
- `--fresh` rebuild, recomputing every stage and re-encoding all audio: about 6 minutes.

- **Stage 20 (D48).** German entries of both Kaikki editions as JSONL with byte-offset indexes. The lexicon now also knows preposition contractions and ordinals.
- **Stage 30.** Still 54,784 lemmas ranked, with the top 2,000 covering 83.2% of running text, and the same 2,000 words as in Phase 1. New: `[merge]` from `words.toml`, and sums that do not depend on set order (needed for byte-identical builds).
  - The first fresh rebuild on the full data was not byte-identical: `token_share` differed in the seventh digit. The cause is Leipzig's multiword units ("Esa-Pekka Salonen"), which share a position with their first word, so "the token before" was ambiguous and DuckDB picked differently on each run. 7,202 Leipzig entries changed their sentence-initial count between two runs.
  - Order is now read from single words only, and a unit opens a sentence when its first word does; units keep their counts (*wie viel* needs them). Since Phase 1, 588 ranks moved, at most 175 places, all in the flat tail; the tricky words kept theirs (*ankommen* went from 642 to 641).
  - The fixture could not show this, since it has no multiword units; `tests/test_leipzig.py` covers it now.
- **Stage 40.**
  - Closed classes from `closed_classes.toml` win over the extracted values.
  - The six modal verbs get their own class, and *wissen* is mixed (D50).
  - Articles, determiners and pronouns get case tables (82% of 56).
  - Numerals get their ordinal (11 of 13; *eins* and *ein* have no link to *erste*).
  - Prepositions list their contractions (*im*, *ins*, *zum*, ...); the ones Wiktionary tags colloquial (*mim*, *fürn*) still count toward the preposition but are not listed.
  - Cognate hints go through the gloss filter (D49).
  - *Herz* and *Schatz* get their plural from the declension table.
- **Stage 50.** 1,997 of 2,000 words have audio, in 1,945 files: some words share a recording, such as the two *Bank* etymologies. ffmpeg is pinned by `flake.lock`, and each file is encoded once per ffmpeg version.
- **Stage 60.** Tatoeba plus Wiktionary usage examples; quotations are never used. Wiktionary fills only 2 sentences (*Story*), because Tatoeba covers nearly everything. Each sentence lists the deck words it contains (`deck_token_ids`, `out_of_deck`) for the app's choice of sentence (D12).
- **Stage 70.** Writes `deck.sqlite` (canonical), `words.json`, `attribution.json`, `coverage.md`, `manifest.json` and the audio. The version is the snapshot's date plus a hash of every input: snapshot, overrides, settings, code and ffmpeg version. `latest.json` names the new deck, so `nix run .#apk` bundles it.
- **Curation data.** `data/work/curation.sqlite` holds 3,922 audio candidates, 39,655 sentence candidates (the best 20 per word), the picks and the QA issues for Phase 4. `data/work/closed-classes.json` holds the evidence that `python -m karteikasten_pipeline.draft` turns into new `closed_classes.toml` entries.
- **Overrides.** Implemented: `words.toml` `[exclude]`, `[merge]`, `[gloss_en]`, `[gloss_de]` and `[no_cognate]`; `closed_classes.toml`; `sentences.toml` `[pin]` and `[ban]`; own recordings. An override that matches nothing fails the build. Pins and splits of ids come when the curation tool needs them.
- **`nix run .#report`** copies the latest deck's coverage to `reports/coverage.md`.

The app shows the new data in the Formen sheet: case tables, contractions, ordinals and the modal class ("Modalverb"). Without this, the Formen hint would open an empty sheet for pronouns.

## Amendments

- **D48 · Stage storage.** Your choice: keep the spike's JSONL and Python stage 20, with stage results cached in `data/work/cache/`.
- **D49 · Cognate filter.** Your choice: a hint ships only when its English word is among the word's English glosses. 283 of 524 hints survive (*und* → and, *Haus* → house, *Jahr* → year, *Hand* → hand). Gone are *schon* → pretty, *sehr* → sorely, *also* → also, but also a few useful ones (*Junge* → young, *Kraft* → craft). Some survivors are archaic English (*du* → thou, *ihr* → ye) because the glosses name them. `[no_cognate]` removes any you dislike.
- **D50 · Modal verbs.** Your choice: a fourth class only where teachers use one, otherwise one of the three.
  - Wiktionary classes *können*, *müssen*, *dürfen*, *sollen*, *mögen*, *wollen* and *wissen* as preterite-present, a historical term.
  - Teaching materials treat the six modal verbs as their own group, *Modalverben* (for example [Rosetta Stone](https://blog.rosettastone.com/types-of-german-irregular-verbs/), [FSI](https://www.fsi-language-courses.org/german/verbs/)). They list *wissen* with the mixed verbs (*brennen*, *bringen*, *denken*, *kennen*, ...; [Grimm Grammar, UT Austin](https://coerll.utexas.edu/gg/gr/vcp_05.html)).
  - So the six verbs in the English edition's "German modal verbs" category get the class `modal`, which the card shows as "Modalverb". *wissen* (weiß, wusste, gewusst) is `mixed`. The class target stays at 100%.

`docs/SPEC.md` has D48–D50 in the amendments table, all accepted,, with stage 20, stage 40, stage 60, the bundle tables and the overrides updated to match.

## Tests

- `pipeline/tests/fixtures/snapshot.tar.gz` (688 KiB) is a slice of every source: the spec's tricky words, every lemma sharing a form with them, and some context. `make_snapshot.py` regenerates it from a full snapshot.
- The real build runs on that slice offline in a few seconds. Tones stand in for the recordings.
- The tests cover the whole tricky-word table, credits, `deck.sqlite`, overrides applying, stale overrides failing, and two builds in separate processes with different hash seeds giving identical bytes.
- Unit tests cover overrides, case and conjunction evidence, case tables, ordinals, the cognate filter, merges, sentence choice with pins and bans, Leipzig's multiword units, the cache and the coverage report.
- `nix flake check`'s `pipeline` and `app` checks pass.

## Housekeeping

- `data/raw/{arasaac,cldr,koeper,openmoji}` (about 20 MB) are leftovers from the pictures (D46). They are no longer in the lock and can be deleted.
- The Phase 1 caches in `data/work/*.pickle` (about 220 MB) are unused now, and `pipeline/karteikasten_pipeline/spike.py` is gone.
- The Phase 3 work is committed (c1d3446 to 8902eaa); the review changes above come after.
