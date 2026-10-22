"""Leipzig Corpora Collection downloads, unpacked under data/work/leipzig/<corpus>/.

<corpus>-words.txt holds (word id, word, count) with case preserved, and
<corpus>-inv_w.txt holds (word id, sentence id, 0-based position) for every token.
The positions let stage 30 tell "Sie" opening a sentence from formal "Sie".

The lists also hold multiword units ("Esa-Pekka Salonen", "wie viel") at the
position of their first word. Their counts stay (multiword lemmas need them),
but which token comes before which is read from single words only: with two
entries at one position "the previous token" is ambiguous, and the counts
varied from run to run. A unit opens a sentence when its first word does.
"""

import tarfile
from pathlib import Path

import duckdb


def unpack(archive: Path, dest: Path) -> Path:
    """Unpack `archive` into `dest` once; return the corpus directory."""
    name = archive.name.removesuffix(".tar.gz")
    corpus = dest / name
    if not (corpus / f"{name}-inv_w.txt").exists():
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as tar:
            tar.extractall(dest, filter="data")
    return corpus


def _tsv(path: Path, columns: str) -> str:
    return f"read_csv('{path}', delim='\t', header=false, quote='', escape='', columns={{{columns}}})"


# A word right after these may be capitalised only because a (quoted) sentence starts there.
OPENERS = ("„", "“", '"', "«", "»", "‚", "‘", "'", ":", ".", "!", "?", "…")


def counts(con: duckdb.DuckDBPyConnection, corpus: Path) -> duckdb.DuckDBPyRelation:
    """Per word form: total occurrences and how many of them are in a position that
    forces a capital: the first token with a letter in the sentence, or a word
    right after an opening quote, colon or sentence-final punctuation."""
    words = _tsv(corpus / f"{corpus.name}-words.txt", "'id': 'BIGINT', 'word': 'VARCHAR', 'freq': 'BIGINT'")
    inv = _tsv(corpus / f"{corpus.name}-inv_w.txt", "'word_id': 'BIGINT', 'sentence_id': 'BIGINT', 'pos': 'INTEGER'")
    openers = ", ".join("'" + mark.replace("'", "''") + "'" for mark in OPENERS)
    return con.sql(
        f"""
        WITH words AS (SELECT *, contains(word, ' ') AS multiword FROM {words}),
        positions AS (SELECT * FROM {inv}),
        tokens AS (
            SELECT p.sentence_id, p.pos,
                   regexp_matches(w.word, '\\p{{L}}') AS lettered,
                   lag(w.word) OVER (PARTITION BY p.sentence_id ORDER BY p.pos) AS previous
            FROM positions AS p JOIN words AS w ON w.id = p.word_id
            WHERE NOT w.multiword
        ),
        first_lettered AS (
            SELECT sentence_id, min(pos) AS pos FROM tokens WHERE lettered GROUP BY sentence_id
        ),
        opening AS (
            SELECT tokens.sentence_id, tokens.pos
            FROM tokens JOIN first_lettered USING (sentence_id)
            WHERE tokens.lettered AND (tokens.pos = first_lettered.pos OR tokens.previous IN ({openers}))
        ),
        opened AS (
            SELECT p.word_id, count(*) AS n
            FROM positions AS p JOIN opening USING (sentence_id, pos)
            GROUP BY p.word_id
        )
        SELECT words.word, words.freq AS total, coalesce(opened.n, 0) AS initial
        FROM words LEFT JOIN opened ON opened.word_id = words.id
        """
    )
