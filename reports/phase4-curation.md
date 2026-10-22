# Phase 4 report: curation and QA

2026-10-22. Deck: `data/dist/deck/2026.10.22-6cfb50a/` (profile `personal`). Coverage per field: `reports/coverage.md`; what changed since the last Phase 3 deck: `reports/diff.md`.

**Your review (2026-10-22):**

1. The tool looks good to you.
2. The 120 syllable/stress warnings stay warnings: no `[syllables]` table. Wiktionary's hyphenation and its IPA count different syllables for those words, so they get no stress highlight; the target (≥ 93%) is met at 93.2%.

Before your first own recording, fill in `[recordings]` `author` and `license` in `config/pipeline.toml` (CC0 is suggested for a release). A build with a recording fails while they are empty.

## Done criterion

| Criterion | Result |
| --- | --- |
| The top 500 words have no blocking issues | Yes, and none in the whole deck. The 10 left after Phase 3 were all abbreviations: *Dr.*, *TU* and *S.* had no gloss or gender, *St.* and *b.* no gloss. D51 settles them from Wiktionary (below). |

## The curation tool

`nix run .#curate` opens a ratatui TUI on `data/work/curation.sqlite`.

- **Queue:** words with issues, blocking first, then by rank; `t` shows every word, `/` searches by lemma. ✎ marks words an override already names.
- **Word view:** the card (glosses, IPA, forms, flags, issues), the audio picker and the sentence picker; Tab moves between the two.
  - **Audio:** every recording Wiktionary links, with author, licence and region. ● is the build's pick, ★ your pin, ◆ your own recording, which wins.
  - `a` pins a candidate in `words.toml` `[audio]`; `x` removes the pin. Space plays.
  - 1,910 candidates the build did not pick are not in the snapshot. Space fetches one first through the pipeline (`fetch --commons FILE`), so what you hear is what a pin ships.
  - **Recorder:** `r` starts a capture into `overrides/audio/<id>.flac`, `r` again stops it.
  - **Sentences:** the best 20 candidates. ● means in the deck, ★ pinned, ✗ banned. `a` pins or unpins in `sentences.toml` `[pin]` (in the order you pin), `x` bans or lifts the ban; a sentence is never both.
- **Saving:** every change is saved at once through toml_edit, so comments and layout in the override files survive and only the touched entries change. The header says when overrides are newer than the database, that is, when the next `nix run .#build` would change the deck.
- **Commands:** `curate/curate.toml` sets `record_cmd`, `play_cmd` and `fetch_cmd`. The wrapper puts ffmpeg, ffplay and the pipeline on PATH.

## Automated checks

The checks are the spec's table, run by every build into `curation.sqlite` and `coverage.md`:
- **Blocking:** noun without gender or plural, verb without Partizip II or auxiliary, no English gloss, any item without licence or author.
- **Warning:** no audio, no sentence, syllable/stress mismatch, audio length outlier.

Two changes:
- Abbreviated nouns need no gender or plural (D51).
- An orphaned override already fails the build (Phase 3), so it never reaches the queue. The spec now says so instead of listing it as a warning.

## Diff report

`nix run .#report -- --diff [OLD [NEW]]` writes `reports/diff.md`. Without versions, it compares the latest deck with the one built before it. It lists:
- which inputs changed;
- words entering and leaving the deck, and the largest rank moves;
- card changes per field (gloss, definition, IPA, article, flags, forms, syllables and stress, cognate, audio, sentences), with examples;
- coverage changes;
- issues fixed and new.

`reports/diff.md` shows this phase against the last Phase 3 deck: 5 glosses and 5 flags changed, 10 blocking issues fixed, no rank moved.

## Pipeline changes

- **D51:** abbreviations take their abbreviation senses as glosses and the flag `abbreviation`.
- **`words.toml` `[audio]`:** the build fails when the file is not one of the word's candidates, or when Commons names no author or licence for it.
- **`curation.sqlite`:** adds `meta` (the deck version), each word's card as JSON, and each candidate's URL.
- **`fetch --commons FILE...`:** adds single Commons recordings to the snapshot.
- **Deck version:** only the Commons recordings the deck uses count toward it, so listening to a candidate in the tool changes nothing. Because this changes how the raw hash is computed, `diff.md` lists `raw` as changed against the Phase 3 deck. No source data changed. `sources.lock.json` now also lists *De-Hand.ogg*, which I fetched while testing playback; no deck uses it.

## Coverage against the targets (top 2,000)

11 of 14 targets are met. English gloss and the three noun fields reached 100% with D51. The other three are your earlier calls:
- **IPA:** *Dr.*, *b.*
- **Audio:** *Dr.*, *b.*, *rauskommen*
- **At least 1 sentence:** *Dr.*, *S.*, *St.*, *b.*

## Amendments

- **D51 · Abbreviations.** Your choice: from Wiktionary.
  - They stay in the deck as everyday vocabulary. A word whose only senses are abbreviations takes them as its English glosses: *Dr.* "abbreviation of Doktor", *St.* "abbreviation of Sankt", *b.* "abbreviation of bei", *S.* "abbreviation of Seite; … of Süden; … of Satz".
  - *TU*'s gloss is Wiktionary's own, typo included: "initialism of Technisch Universität".
  - Abbreviated nouns are exempt from the gender, plural and genitive checks and coverage fields.

`docs/SPEC.md` has D51, `[audio]` under Overrides, the curation tool's keys, commands and fetching, the diff report, and the deck-version rule.

## Tests

- **pytest:** 141 pass. New tests cover D51, `[audio]` (applies, fails when stale), the diff report (words, ranks, fields, issues, syllable checks from the deck alone), and a build check that a fetched but unused recording leaves the deck version alone.
- **cargo test:** 10 pass, including the spec's round trip. The real override files parse and print back byte for byte, and an edit undone leaves a file as it was. Other tests cover pins and bans excluding each other, queue order, command templates with spaces in file names, and drawing the real database.
  - Under Nix the build sees only `curate/`, so the real-file round trip runs in the dev shell; inline samples of the same shapes run everywhere.
- **clippy:** clean with warnings denied.
- **`nix flake check`:** passes.

Committed after your review.
