# Phase 1 report: data spike

2026-10-06. Inputs: the 12 sources pinned in `sources.lock.json` (field notes in `docs/sources/`).
Throwaway deck: `data/dist/deck/2026.10.06-bdc9ce1-spike/` (top 100 plus *Hand* and *fahren*; gitignored, not a release).

**Decided 2026-10-06:** amendments D23–D26 accepted (D24 and D26 with your refinements), recorded in `docs/SPEC.md`.

**Still needs you:** the curation calls under "Anomalies" (or leave them for the curation tool).

**2026-10-15:** pictures are gone (D46), and with them the concreteness labels. The image findings below stay as a record.

**Decided 2026-10-22:** the coverage targets in the last section are confirmed as proposed.

## Summary

- Fetch works for all sources: polite User-Agent with contact, at most 2 requests per second per host, retries with backoff, resumable downloads, every raw file hashed in the lock.
- Stages 20 (lexicon), 30 (frequency), 40 (card content), 50 (media), 60 (sentences) and 70 (bundle) all run as spike code. 44 pytest tests pass.
- The blended list ranks 54,784 lemmas. Text coverage is **58.1%** for the top 100, **73.4%** for 500, **78.6%** for 1,000 and **83.2%** for 2,000. 5.6% of blended mass matches no lemma (English words, names, *mr.*, *hey* from subtitles).
- Content coverage for the top 2,000 is high: 99.8% have English glosses, 96.6% German definitions, 99.9% IPA and 99.9% audio. 99.8% have Tatoeba sentences, and for 99.7% the best one is by a native author with an English translation. Gaps are listed below.
- Four findings contradict the spec. They are proposed below as amendments D23–D26, and nothing changed silently.

Top 40: der (article), sein (verb), ich, ein (article), und, haben, in, nicht, es, Sie, werden, wir, du, mit, der (pronoun), er, können, zu (prep), von, auf, was, für, zu (particle), an, dass, sie, sie, dieser, sich, so, all, gut, auch, wie (conj), wollen, müssen, wenn, als, noch, hier.

## Verify in Phase 1: answers

- [x] **Is FrequencyWords case-folded? Does Leipzig keep case? Which Leipzig corpora?** FrequencyWords is fully lower-cased. Leipzig keeps case and records each token's position. Corpora: `deu_news_2025_1M` and `deu-de_web_2021_1M`, the newest of each; no German web corpus exists after 2021. Case ratios skip sentence-initial and quote-initial positions (see `docs/sources/leipzig.md`).
- [x] **Kaikki field paths for forms, tags, sounds, hyphenation and examples in both editions:** documented in `docs/sources/kaikki.md`, with the traps each edition has.
- [x] **Audio coverage, speaker distribution, preferred Lingua Libre speaker:**
  - 99.9% of the top 2,000 have a standard-German Commons recording.
  - Lingua Libre covers only 3.8%. Sebastian Wallroth is the top speaker with 65 words.
  - One Commons author, **Jeuwre, has recordings for 98.75%** (1,975) of the top 2,000, hence D24.
  - Under D24 the other 22 words fall through to 7 authors, next by coverage. The spike deck now has one voice for 101 of its 102 words (*ja* is by MiER).
  - No candidate audio is NC or ND.
- [x] **Concreteness thresholds:** dropped with the pictures (D46).
- [x] **ARASAAC endpoints, rate limits, match rate; OpenMoji/CLDR match rate:**
  - Endpoints were in `docs/sources/arasaac.md`, removed with D46 (still in git history). A single `GET /v1/pictograms/all/de` replaces about a thousand searches. No rate limit is published, so the client allows at most 2 requests per second.
  - Of the 791 nouns in the top 2,000, ARASAAC matches 476 (60%), OpenMoji/CLDR 309 (39%) and either one 535 (68%), before the concreteness filter and approval.
- [x] **Licences of UD GSD and HDT, and the terms of the Köper norms:**
  - GSD: CC BY-SA 4.0.
  - HDT: annotation CC BY-SA 4.0, but the text is for academic use only. Fine, since only ratios are used.
  - Köper: **CC BY-NC-SA 4.0**, hence D26.
- [x] **Separable-verb correction:**
  - Ranks: *anfangen* #382, *anrufen* #426, *aufhören* #466, *ankommen* #642.
  - DeReWo cross-check (numbers only in the private `data/work/derewo/crosscheck.md`): all four rank considerably more frequent here than in the written-only DeReWo list. That's plausible for words much more common in speech than in news, so I consider it plausible.
  - The overall rank agreement with DeReWo is moderate, as expected for a list weighted 70% to subtitles.
- [x] **Tatoeba files, native-speaker yield, review tags:**
  - Files and URLs are in `docs/sources/tatoeba.md`.
  - 613,268 of 782,626 German sentences (78%) are by native (level 5) authors.
  - Review tags: `@needs native check`, `@check`, `@change`, `@delete`, `unnatural`, `wrong grammar` and variants (359 sentences carry one).
- [x] **Coverage targets per field for Phase 3:** confirmed on 2026-10-22; see the last section.

## Coverage per field

| Field | Top 100 | Top 500 | Top 2000 | Source |
| --- | --- | --- | --- | --- |
| English gloss | 100% | 99.8% | 99.8% | English Wiktionary |
| German definition | 92% | 94.2% | 96.6% | German Wiktionary |
| IPA | 100% | 99.8% | 99.9% | German Wiktionary (Germany), else English |
| Syllables | 99% | 99% | 99.2% | German Wiktionary hyphenation |
| Stress highlight | 95% | 93.6% | 93.2% | IPA stress mark; none when syllable counts disagree |
| Cognate hint | 44% | 42.6% | 26.2% | English-edition etymology (quality: see Anomalies) |
| Noun gender / plural only | 5 of 5 | 99.2% | 99.6% of 791 | English Wiktionary sense tags |
| Noun plural (or flag) | 5 of 5 | 99.2% | 99.5% | English Wiktionary forms |
| Noun genitive | 5 of 5 | 98.3% | 99.4% | English Wiktionary forms |
| Noun table with articles | 5 of 5 | 98.3% | 98.4% | German Wiktionary forms |
| Verb er-form, Präteritum, Partizip II, auxiliary | 18 of 18 | 100% | 100% of 560 | English Wiktionary forms |
| Verb strong/weak/mixed | 67% | 94.6% | 98.8% | English Wiktionary tags (modals are missing) |
| Adjective comparison | 3 of 4 | 80.3% | 78.5% of 297 | Forms; ordinals and non-gradable adjectives have none |
| Preposition case | 86% | 80% | 76% of 42 | German Wiktionary tags; `closed_classes.toml` will decide |
| Conjunction type | 78% | 88% | 94% of 31 | German Wiktionary `pos_title` |
| Audio | 100% | 99.8% | 99.9% | Commons via both editions; one voice for 98.75% (D24) |
| Image candidate (nouns) | n/a | n/a | 68% of nouns | ARASAAC or OpenMoji; before the concreteness filter and approval |
| 5 sentences | 100% | 99.8% | 99.5% | Tatoeba, 4–10 tokens, no review tags |
| Best sentence native with English | 100% | 99.8% | 99.7% | Tatoeba |

Word types in the top 2,000: 791 nouns, 560 verbs, 297 adjectives, 192 adverbs, 40 prepositions, 37 pronouns, 31 conjunctions, 17 determiners, 16 interjections, 13 numerals, plus 2 each of articles, particles and postpositions.

## Tricky words (spec test table)

| Word(s) | Result |
| --- | --- |
| sein (verb) / sein (det) | Two ids, `sein#verb#1` @2 and `sein#det#2` @50. The possessive is etymology 2 in Wiktionary, so the id rule gives `#2`, not the spec example's `#1`. |
| die | Split into article (`der#article#1` @1) and pronoun (`der#pron#1` @15) by UD (88.5% / 11.5%). |
| Bank (Bänke) / Bank (Banken) | `Bank#noun#2` (bank) @815, `Bank#noun#1` (bench) @4389. *Bänke*/*Banken* go to the right etymology; shared forms split by the mass of each etymology's own forms. |
| Essen/essen, Morgen/morgen, Sie/sie | Separate ids: Essen @530, essen @422, Morgen @331, morgen @413, Sie @10, sie @26/@27 (see Anomalies). |
| anfangen, aufhören, ankommen, anrufen | @382, @466, @642, @426: plausible (see above). |
| Junge, Herr | Weak-noun flag; genitives *Jungen*, *Herrn*. |
| Leute, Eltern | Plural-only flag, article *die*. |
| haben, werden, können, wissen, fahren | Forms present (*hat/hatte/gehabt*, *wird/wurde/geworden* + sein, *kann/konnte*, *weiß/wusste*, *fährt/fährst/fuhr/gefahren* + haben/sein). Modals lack a strength flag. |
| sich freuen | Reflexive flag (weak verb). |
| gut, viel, gern, hoch | besser / am besten; mehr / am meisten; lieber / am liebsten; höher / am höchsten, irregular stem *hohe*. |
| mit, für, in, wegen | dative, accusative, two-way, genitive (dative colloquial). |
| weil, und | subordinating, coordinating. |
| doch, mal | Particle flag ("kontextabhängig") from German Wiktionary's *Modalpartikel*/*Antwortpartikel* entries. But *doch* is split across three cards (see Anomalies). |
| ja, danke, okay | Kept: ja @51, danke @439, okay @190 (adj) / @847 (interj). |
| äh | Excluded via `overrides/words.toml`. |

## Anomalies

1. **One learner word, several cards.** Ids are `lemma#pos#n`, so wherever Wiktionary splits a word by POS, the deck gets several cards. In the top 500:
   - Intended: *der* (article/pronoun), *sein* (verb/possessive), *Moment* (der/das, two meanings).
   - Probably one card each: *sie* she/they (@26/@27, split 50/50 because UD can't separate them), *ihr* (two possessive etymologies plus the pronoun), *doch* (conj @90, adv @135, particle), *aber* (adv @44, conj @87), *zu* (prep, infinitive particle, "too"), *wie*, *da*, *denn*, *um*, *über*, *viel*, *etwas*, *ja*, *okay*, *welcher*, *gleich*, *anderer*.
   - These are curation decisions for `overrides/words.toml` (merges). Tell me which to merge, or I'll leave them for the curation tool.
2. **Written UD splits spoken words.** POS splits come from UD's news and web text. So *ja* is mostly the modal-particle adverb (@51) rather than the answer interjection (@488). And *okay* splits evenly between adjective and interjection, because UD never saw it.
3. **Formal *Sie*** gets 53% of non-initial *sie/Sie* in Leipzig, because the web corpus is full of formal address. Subtitles may differ. This affects *Sie* (@10) vs *sie*.
4. **Stress highlight:** 120 of the top 2,000 (6%) have different syllable counts in hyphenation and IPA. German hyphenation never separates a single-vowel first syllable (*aber*, *über*, *Abend*, *Idee*, *Problem*). Per spec these get no highlight; IPA alone would cover them, if you want that.
5. **Cognate hints are noisy.** Good: *ein*→one, *und*→and, *Hand*→hand, *Jahr*→year. Misleading: *schon*→pretty, *sehr*→sorely, *wieder*→wither, *nach*→nigh, *auch*→eke. The spec's exceptions list is needed. Expect roughly half of the raw hints to survive.
6. **Modal verbs** (*können*, *wissen*) carry no strong/weak/mixed tag in Wiktionary.
7. **Ordinals** (*zweite* for *zwei*) are not linked from numeral entries. Numeral key forms will need `closed_classes.toml` or a lookup by the ordinal entries' etymology.
8. **Preposition case** is tagged for most core prepositions but not all (76%). `closed_classes.toml` (hand-checked, per spec) will close the gap.
9. **Lemma conventions differ between UD and Wiktionary** (*alle* vs *all*; *Leute* vs archaic *Leut*). Handled: UD evidence is matched by POS first, and archaic entries give way to current ones.
10. **Letters and abbreviations rank high.** 15 of the top 2,000 are single letters or abbreviations that have Wiktionary entries, so the filter keeps them: *S* @161, *Dr.* @303, *TU* @650, *N*, *A*, *S.*, *I*, *M*, *O*, *St.*, *E*, *B*, *D*, *b.*, *T*. Most are corpus noise (initials, list markers). Excluding them is a curation call for `overrides/words.toml`. *Dr.* and *b.* also have no recording.

## Amendments (accepted 2026-10-06)

- **D23: Kaikki English edition source file.** Accepted.
  - The spec names the per-language German JSONL, which Kaikki has deprecated "for removal" (issue #1178). Kaikki recommends the full raw dump filtered by `lang_code`.
  - Proposal: use `raw-wiktextract-data.jsonl.gz` (2.98 GB download) and extract the German entries once per snapshot. Already implemented this way.
- **D24: Audio speaker preference.** Accepted, refined: below the top author, words fall through to authors with less and less coverage (not to "Germany-tagged, then any").
  - The spec prefers "the Lingua Libre speaker covering most of the deck", but Lingua Libre covers only 3.8% of the top 2,000. One Commons author (Jeuwre) covers 98.7%, so the current rule mixes in a second voice for about 3% of words.
  - Proposal: prefer the Commons author (any project) covering most of the deck, then Germany-tagged, then any German file, regional last. Own recordings still win.
  - Implemented in `stages/media.py` with tests. The old rule mixed voices far more than the 3% estimated above: below the Lingua Libre speaker it went by Germany tag, then file name, so Kampy's `De-gut.ogg` beat Jeuwre's `De-gut2.ogg`. A quarter of the old spike deck (26 of 102 words) had a voice other than Jeuwre's. Spike and fixture decks are rebuilt.
  - Commons metadata is now looked up per title across all snapshots, so a changed word list only asks for new titles. Before, a shifted list moved every batch boundary and refetched nearly everything, which is what happened once while I rebuilt the decks (71 batches).
- **D25: Separable verbs, the other half of the correction.** Accepted.
  - Scaling particle verbs by the split/unsplit ratio (0.51 overall) adds their split uses, but those uses are also still counted twice elsewhere: as the base verb (*fängt … an* → *fangen*) and as a preposition (*an*).
  - Proposal: also discount each base verb by the UD share of its tokens that head a separated particle, and each particle token by its UD share of separated-particle (PTKVZ) uses. Implemented; without it, *an*, *auf* and *aus* are overcounted.
- **D26: Köper norms are NC.** Accepted. `personal` is the development build and uses the whole data set, norm-derived `is_concrete` included.
  - `is_concrete` in the shipped deck is derived from CC BY-NC-SA data.
  - Proposal: the public profile ships `is_concrete` only where a human approved or rejected an image. The norms stay a build-time pre-filter for candidates, which never ship.

## Coverage targets for Phase 3 (top 2,000, after curation)

Proposed with this report and confirmed on 2026-10-22.

| Field | Target |
| --- | --- |
| English gloss, IPA, audio, ≥1 sentence | 100% (each gap is fixed by curation or an own recording) |
| German definition | ≥ 95% |
| Noun gender, plural or flag, genitive | 100% |
| Verb core forms and auxiliary | 100% |
| Verb strength flag | ≥ 98% (modals via `closed_classes.toml`) |
| Preposition case, conjunction type | 100% (`closed_classes.toml`) |
| Stress highlight | ≥ 93% (spec rule) |
| 5 sentences | ≥ 99% |
| Cognate hint | no coverage target; 0 wrong hints after the exceptions list |
