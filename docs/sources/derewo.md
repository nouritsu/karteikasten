# DeReWo (IDS Mannheim): private cross-check only

Never shipped, never committed. `.gitignore` blocks `*derewo*.txt|zip` anywhere, and the numbers live only in `data/work/derewo/crosscheck.md`.

- File: `derewo-v-ww-bll-320000g-2012-12-31-1.0.zip` (326,946 lemmas, 2012). You downloaded it by hand; `fetch` records it in the lock but never downloads it. The zip holds the list and two PDFs of documentation, which the terms require to stay with the list.
- Licence: the list's own header says CC BY-NC 3.0. The IDS page adds: no commercial use, and no referencing or passing on without the documentation.
- Format: ISO-8859-15. `#` lines are a header; then `lemma frequency-class [POS]`, ordered by frequency, so a lemma's rank is its line number. Some lemmas are grouped (`der,die,das 0 DET`).
- Use: Phase 1 cross-check of the separable-verb correction and of the overall ranking. Only verdicts, never DeReWo numbers, appear in committed reports.
