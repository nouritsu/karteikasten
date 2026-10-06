# Kaikki (wiktextract): English and German Wiktionary

POS, gender, forms, glosses, IPA, audio links, etymology, examples. Ships: yes (CC BY-SA 4.0 and GFDL, credited).

## English edition

- **The spec's file is deprecated.** The per-language German JSONL on kaikki.org (1.0 GB) is marked "DEPRECATED, will be removed" (wiktextract issue #1178), and Kaikki now recommends the full raw dump filtered by `lang_code`. So the fetcher takes `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` (2.98 GB; 23.9 GB uncompressed; enwiktionary dump 2026-09-02). Accepted as amendment D23.
- German entries, extracted once into `data/work/kaikki/en.jsonl`: 371,261 (139 s). A substring check on `"lang_code": "de"` only pre-filters, because English entries' translation lists contain it too, so each candidate line is parsed and checked at the top level.
- Field paths used:
  - `word`, `pos` (`noun`, `verb`, `adj`, `adv`, `article`, `det`, `pron`, `prep`, `postp`, `conj`, `particle`, `intj`, `num`, `contraction`, `name`, …).
  - `etymology_number`: a string, present on only 3,913 entries; default 1.
  - `senses[].glosses`: the last element is the most specific gloss.
  - `senses[].tags`: gender (`masculine`/`feminine`/`neuter`), `plural-only`, `weak` (noun), `strong`/`weak`/`irregular` (verb), `reflexive`, `vulgar`, register labels.
  - `senses[].form_of[].word` and `senses[].alt_of[].word`.
  - `forms[]`: `form` with `tags` (`nominative`, `plural`, `third-person`, `preterite`, `participle`, `past`, `auxiliary`, `comparative`, `superlative`, `subordinate-clause`, …).
  - `sounds[]`: `ipa`, `audio`, `ogg_url`, `mp3_url`, `tags` (`Germany`, `Berlin`, `Austria`).
  - `hyphenations[].parts`: rare in this edition (52k entries).
  - `etymology_text`.
  - `head_templates[].expansion`, e.g. "Hand f (genitive Hand, plural Hände, …)".
- Traps (all handled in `stages/lexicon.py`):
  - Entries sharing (word, POS, etymology) are one lemma: *Hand* also has a separate "clipping of *Handspiel*" entry.
  - `forms` contains template debris: rows tagged `table-tags`, `inflection-template`, `class` ("7 strong") or `auxiliary` (*haben*, which is not a form of *anfangen*).
  - Personal-pronoun entries list the whole paradigm as forms, tagged `personal`, so *Sie* lists *ich*, *du*, *er*.
  - Proper nouns list their article as a `canonical` form (*die* for *CIA*).
  - *sie* etymology 3 is "misspelling of Sie"; misspelling entries are skipped.
  - Obsolete alternative spellings (*das* for *dass*) don't count as forms.
  - A form spelled with a different initial case than its lemma is another word: archaic *Er* lists *er*.
  - Contractions (*im*, *zum*, *am*) have their own entries; the gloss names the preposition: "contraction of an (“at/on”) + dem".
  - Separable verbs show as two-word forms (*fängt an*). Verb-final forms (*anfängt*) exist both as form-of entries and in `forms` tagged `subordinate-clause`.
  - IPA comes both phonemic (`/hant/`) and phonetic and regional (`[hɑnd̥]`).

## German edition

- `https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz` (309 MB). German entries extracted into `data/work/kaikki/de.jsonl`: 1,010,306, including inflected-form entries.
- Field paths used:
  - `pos` plus `pos_title` (*Substantiv*, *Hilfsverb*, *Subjunktion* vs *Konjunktion*, *Modalpartikel*, *Antwortpartikel*, *Deklinierte Form*, …).
  - Entry-level `tags` for noun gender.
  - `hyphenations[].parts` (99% of entries).
  - `sounds[]`: `ipa` as Germany-standard phonetic transcription in brackets, with ˈ/ˌ stress marks, plus `audio` with `ogg_url`/`mp3_url`.
  - `senses[].glosses` (strip footnote markers like `^([1])`), `senses[].examples[]` with `text`, `ref` and `bold_text_offsets`.
  - `senses[].tags` `with-dative`/`with-accusative` for prepositions; *wegen* has it only as raw text ("Präposition mit Genitiv, mit Dativ").
  - `forms[]` with case and number tags **and the `article`**, which gives full noun tables with articles.
- Hyphenation never splits off a single-vowel first syllable (*Abend*, *Ofen*, *Ele·fant*, *aber*, *über*). That is the main source of hyphenation/IPA syllable-count mismatches: 120 of the top 2,000.
- Stable ids follow the spec (`lemma#pos#n`, n the English edition's etymology number): `Bank#noun#1` (*Bänke*) and `Bank#noun#2` (*Banken*). Note that the possessive *sein* is etymology 2, so its id is `sein#det#2`, not the spec's example `sein#det#1`.
