import json

from karteikasten_pipeline import diff


def word(id_, rank, **fields):
    lemma, pos, _ = id_.split("#")
    base = {"id": id_, "lemma": lemma, "pos": pos, "rank": rank, "gloss_en": [{"text": lemma, "tags": []}],
            "gloss_de": [], "ipa": "[x]", "article": None, "flags": [], "key_forms": {}, "tables": {},
            "syllables": [lemma], "stress_syllable": 0, "cognate_en": None, "audio": None, "sentences": []}
    return {**base, **fields}


def deck(tmp_path, version, words, **inputs):
    directory = tmp_path / version
    directory.mkdir()
    manifest = {"deck_version": version, "inputs": {"raw": "a", "code": "a", **inputs}}
    (directory / "manifest.json").write_text(json.dumps(manifest))
    (directory / "words.json").write_text(json.dumps(words))
    return diff.Deck.load(directory)


def test_diff_lists_words_ranks_fields_and_issues(tmp_path):
    old = deck(tmp_path, "v1", [word("Haus#noun#1", 1, article="das"), word("Tür#noun#1", 2),
                                word("alt#adj#1", 3)])
    new = deck(tmp_path, "v2", [word("Tür#noun#1", 1, article="die", key_forms={"plural": "Türen"}),
                                word("Haus#noun#1", 2, article="das", ipa="[haʊ̯s]"), word("neu#adj#1", 3)],
               code="b")
    text = diff.render(old, new)
    assert "deck v1 → v2" in text and "Inputs changed: code." in text
    assert "Entered (1): *neu* (adj, #3)" in text and "Left (1): *alt* (adj, #3)" in text
    assert "| *Tür* (noun) | 2 | 1 |" in text
    assert "### IPA (1)" in text and "| *Haus* (noun, #2) | [x] | [haʊ̯s] |" in text
    assert "### Article (1)" in text
    assert "`Tür#noun#1` noun-gender" in text  # fixed: Tür has its gender now


def test_diff_finds_syllable_stress_mismatches_from_the_deck(tmp_path):
    ok = word("Abend#noun#1", 1, ipa="[ˈaːbn̩t]", syllables=["A", "bend"])
    bad = word("Abend#noun#1", 1, ipa="[ˈaːbn̩t]", syllables=["A", "ben", "d"], stress_syllable=None)
    text = diff.render(deck(tmp_path, "v1", [ok]), deck(tmp_path, "v2", [bad]))
    assert "new: `Abend#noun#1` syllable-stress" in text


def test_previous_skips_phase_one_decks(tmp_path):
    for version in ("2026.10.06-a-spike", "2026.10.22-b", "2026.10.22-c"):
        deck(tmp_path, version, [])
    assert diff.previous(tmp_path, "2026.10.22-c") == "2026.10.22-b"
