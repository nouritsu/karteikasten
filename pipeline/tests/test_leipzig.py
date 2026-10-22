import duckdb

from karteikasten_pipeline.readers import leipzig


def corpus(tmp_path, words, tokens):
    directory = tmp_path / "deu_test_1M"
    directory.mkdir()
    (directory / "deu_test_1M-words.txt").write_text("".join(f"{i}\t{w}\t{n}\n" for i, w, n in words))
    (directory / "deu_test_1M-inv_w.txt").write_text("".join(f"{w}\t{s}\t{p}\n" for w, s, p in tokens))
    return directory


def test_multiword_units_keep_their_counts_but_cannot_hide_the_previous_token(tmp_path):
    # Sentence 1: „ Sie kommt   (with the unit "Sie kommt" at position 1, beside "Sie")
    # Sentence 2: Heute kommt sie
    words = [(1, "„", 1), (2, "Sie", 1), (3, "kommt", 2), (4, "Sie kommt", 1), (5, "Heute", 1), (6, "sie", 1)]
    tokens = [(1, 1, 0), (2, 1, 1), (4, 1, 1), (3, 1, 2), (5, 2, 0), (3, 2, 1), (6, 2, 2)]
    counts = {w: (t, i) for w, t, i in leipzig.counts(duckdb.connect(), corpus(tmp_path, words, tokens)).fetchall()}
    assert counts["Sie kommt"] == (1, 1)  # opens the sentence with its first word
    assert counts["Sie"] == (1, 1)  # after an opening quote: its capital says nothing
    assert counts["sie"] == (1, 0) and counts["Heute"] == (1, 1)
