# FrequencyWords: OpenSubtitles 2018 (de)

Spoken word-form counts. Ships: derived ranks only.

- Where: `hermitdave/FrequencyWords`, `content/2018/de/de_full.txt`, pinned to commit `072bbed` (2019-02-13, the last change to that file).
- Licence: content CC BY-SA 4.0 (the repository's code is MIT).
- Format: one `word count` pair per line, space-separated, sorted by count. 1,157,685 lines, 156,169,536 tokens.
- **Case-folded.** No line contains a capital letter, so *Sie/sie*, *Essen/essen* and *Morgen/morgen* arrive merged. Stage 30 splits every lower-case key over the spellings the lexicon knows, using Leipzig's case ratios (see `leipzig.md`).
- Tokens include contractions (*im*, *zum*), separated verb particles (*an* in *fängt … an*) and subtitle noise (names, interjections). Stage 30 handles each of these, see `pipeline/karteikasten_pipeline/stages/frequency.py`.
