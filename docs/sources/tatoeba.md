# Tatoeba: sentences and translations

Ships: yes, each sentence credited to its author with its licence (CC BY 2.0 FR, or CC0 for the sentences in the CC0 lists), linking tatoeba.org.

- Weekly exports at unversioned URLs, so they are snapshotted and locked: `https://downloads.tatoeba.org/exports/per_language/`.
  - `deu/deu_sentences_detailed.tsv.bz2`: `id, lang, text, username, added, modified`. 782,626 German sentences; `\N` means null.
  - `deu/deu-eng_links.tsv.bz2`: German id to English id. 496,750 German sentences have an English link.
  - `eng/eng_sentences_detailed.tsv.bz2` for the English text and its author.
  - `deu/deu_tags.tsv.bz2`: `sentence_id, tag`.
  - `deu/deu_user_languages.tsv.bz2`: `lang, level 0–5, username, details`. 1,242 users at level 5 (native).
  - `deu/deu_sentences_CC0.tsv.bz2` and `eng/eng_sentences_CC0.tsv.bz2` list the CC0 sentences.
- Open these files with `newline=''`: a stray `\r` in some fields breaks universal-newline reading.
- Native-speaker yield: 613,268 of 782,626 German sentences (78%) are by level-5 users.
- Review tags (skipped): `@needs native check`, `needs native check`, `@check`, `@change`, `@delete`, `delete`, `unnatural`, `wrong grammar`, `@check translation`, `check translation`, `@change punctuation`, `@change or unlink`, `@change flag`, `@check link(s)`, `@check copyright`. 359 German sentences carry one. `OK` (9,443) is a positive review tag.
- Top 2,000: 99.8% of words have at least one sentence with 4–10 tokens, and 99.5% have five. For 99.7% the best sentence is by a native author and has an English translation.
