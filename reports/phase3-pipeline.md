# Phase 3 report: full pipeline (n = 2,000)

2026-10-22. Deck: `data/dist/deck/2026.10.22-640b71e/` (profile `personal`; the `public` build is `2026.10.22-e4fcf1a`). Kaikki, Tatoeba and the corpora are the 2026-10-06 snapshot; the Commons audio was fetched today. Coverage per field: `reports/coverage.md`.

**Still needs you:**

1. Check `overrides/closed_classes.toml`. I drafted it from both Wiktionary editions; the comment above each entry says what they say.
   - The editions disagree on 8 entries, marked CHECK: *vor*, *über*, *ab*, *neben*, *pro*; *als*, *weil*, *sowie*.
   - 2 have no evidence and are commented out for you to fill in: the postposition *lang* and *doch* as a conjunction.
2. Decide on the 15 letters and abbreviations in the top 2,000 (*Dr.*, *TU*, *S.*, *St.*, *b.*, *S*, *N*, *A*, *I*, *M*, *O*, ...). They cause all the remaining gloss, IPA, sentence and noun gaps, and two of the three audio gaps. Exclude them in `overrides/words.toml` `[exclude]`, or give them glosses in `[gloss_en]`. Excluding them moves 15 new words into the top 2,000.
3. *rauskommen* (rank 1,500) has no recording linked from either edition. Closing that gap takes an own recording in `overrides/audio/` (and your name and licence under `[recordings]` in `config/pipeline.toml`), or you accept it.
4. Accept or reject D50 (below).

Optional: the multi-card words from Phase 1 (*sie* ×2, *ihr* ×3, *doch*, *aber*, *zu*, ...) can now be merged with `[merge]` in `words.toml`.

## Done criteria

| Criterion | Result |
| --- | --- |
| Two builds from the same snapshot are byte-identical | Yes, after a fix in stage 30 (below). Two `--fresh` builds in separate processes, with hash seeds 13 and 17, and a cached rebuild with seed 5 give the same 1,950 files (digest `1625cdb1…`). The fixture test does the same in pytest. |
| Every media item and sentence has source, author and licence | Yes. The build skips sentences and translations without a named author; the checks find no item without a credit. |
| pytest passes the tricky-word fixtures | Yes. 126 tests pass in the Nix check; 6 more check the real deck and pass here (the sandbox has no `data/`). |
| The coverage targets set in Phase 1 are met | 5 of 14 now. The other 9 come down to the calls above (next section). |

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
| Preposition case | 97.6% | 100% | *lang* (postposition) |
| Conjunction type | 96.8% | 100% | *doch* (conjunction) |
| Stress highlight | 93.2% | ≥ 93% | met |
| 5 sentences | 99.5% | ≥ 99% | met |
| Cognate hint | 283 hints | 0 wrong | your judgement; see D49 |

With the abbreviations settled and *lang* and *doch* filled in, every target is met except *rauskommen*'s audio. The only blocking issue left in the top 500 is *Dr.* (no gender, no gloss).

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
  - Modal verbs get the preterite-present class (D50).
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

The app shows the new data in the Formen sheet: case tables, contractions, ordinals and the preterite-present class. Without this, the Formen hint would open an empty sheet for pronouns.

## Amendments

- **D48 · Stage storage.** Your choice: keep the spike's JSONL and Python stage 20, with stage results cached in `data/work/cache/`.
- **D49 · Cognate filter.** Your choice: a hint ships only when its English word is among the word's English glosses. 283 of 524 hints survive (*und* → and, *Haus* → house, *Jahr* → year, *Hand* → hand). Gone are *schon* → pretty, *sehr* → sorely, *also* → also, but also a few useful ones (*Junge* → young, *Kraft* → craft). Some survivors are archaic English (*du* → thou, *ihr* → ye) because the glosses name them. `[no_cognate]` removes any you dislike.
- **D50 · Modal verbs (proposed).** Wiktionary classes *können*, *müssen*, *dürfen*, *sollen*, *mögen*, *wollen* and *wissen* as preterite-present, not strong, weak or mixed. I propose carrying that as a fourth verb class instead of forcing them into the three, so the class target is met from the data rather than from `closed_classes.toml`. The card shows "Präteritopräsens". If you reject it, these seven words carry no class, and the class target is still met at 98.75%.

`docs/SPEC.md` has D48–D50 in the amendments table, with stage 20, stage 40, stage 60, the bundle tables and the overrides updated to match.

## Tests

- `pipeline/tests/fixtures/snapshot.tar.gz` (688 KiB) is a slice of every source: the spec's tricky words, every lemma sharing a form with them, and some context. `make_snapshot.py` regenerates it from a full snapshot.
- The real build runs on that slice offline in a few seconds. Tones stand in for the recordings.
- The tests cover the whole tricky-word table, credits, `deck.sqlite`, overrides applying, stale overrides failing, and two builds in separate processes with different hash seeds giving identical bytes.
- Unit tests cover overrides, case and conjunction evidence, case tables, ordinals, the cognate filter, merges, sentence choice with pins and bans, Leipzig's multiword units, the cache and the coverage report.
- `nix flake check`'s `pipeline` and `app` checks pass.

## Housekeeping

- `data/raw/{arasaac,cldr,koeper,openmoji}` (about 20 MB) are leftovers from the pictures (D46). They are no longer in the lock and can be deleted.
- The Phase 1 caches in `data/work/*.pickle` (about 220 MB) are unused now, and `pipeline/karteikasten_pipeline/spike.py` is gone.
- Nothing is committed. The new files are marked with `git add -N` so that Nix sees them.
