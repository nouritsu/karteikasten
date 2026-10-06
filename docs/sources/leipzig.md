# Leipzig Corpora Collection: German news + web

Written word-form counts and case ratios. Ships: derived ranks only.

- Corpora: `deu_news_2025_1M` (news 2025, 17.5M tokens) and `deu-de_web_2021_1M` (German web from .de domains 2021, 17.3M tokens), 1M sentences each. These are the newest of each kind. Probing the download server found news 2022–2025, `deu-de_web` 2020 and 2021 (none after 2021), plus `deu_wikipedia_2021`, `deu_newscrawl-public_2019` and `deu_mixed-typical_2011`.
- Where: `https://downloads.wortschatz-leipzig.de/corpora/<name>.tar.gz`. The website itself sits behind an anti-bot challenge, and Leipzig's terms forbid automated querying, so the fetcher only ever touches these download files.
- Licence: CC BY (per the spec; the tarballs contain no licence file).
- Format (unpacked to `data/work/leipzig/<name>/`):
  - `<name>-words.txt`: `id \t word \t count`. **Case is kept** (*sie* 95,614 vs *Sie* 153,516 across both corpora). Punctuation counts as tokens.
  - `<name>-inv_w.txt`: `word id \t sentence id \t position`, one row per token, positions 0-based. This lets stage 30 count a spelling only where its case is not forced by position.
  - `<name>-sentences.txt`: `id \t sentence`.
- Case ratios ignore any token that is the first word of the sentence or comes right after an opening quote, colon or sentence-final punctuation. Without that rule, 10% of *ich* tokens show up as capitalised *Ich* (quoted speech); with it, 0.8%.
- Known bias: the web corpus is full of formal address, so formal *Sie* gets 53% of non-initial *sie/Sie*. Subtitles may differ.
- Parsing: read with DuckDB `read_csv(..., quote='', escape='')`, because `"` is a token.
