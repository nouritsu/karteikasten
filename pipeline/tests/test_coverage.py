from karteikasten_pipeline import coverage


def word(id_, pos="noun", **fields):
    base = {"id": id_, "rank": 1, "pos": pos, "gloss_en": [{"text": "x"}], "gloss_de": [], "ipa": "[x]",
            "audio": None, "sentences": [], "article": "das", "key_forms": {}, "flags": [], "tables": {},
            "stress_syllable": 0, "syllables": ["x"], "cognate_en": None}
    return {**base, **fields}


def test_targets_and_gaps():
    words = [word("Haus#noun#1", rank=1, key_forms={"plural": "Häuser", "genitive": "Hauses"}),
             word("Leute#noun#1", rank=2, flags=["plural_only"], article="die")]
    field = {f.key: f for f in coverage.FIELDS}
    assert coverage.met(words, field["noun_genitive"])  # plural-only nouns need no genitive singular
    assert not coverage.met(words, field["audio"])
    assert coverage.gaps(words, field["audio"]) == ["Haus#noun#1", "Leute#noun#1"]
    text = coverage.render(words, deck_version="v", profile="personal", extra={"Note": "x"})
    assert "| Audio |" in text and "Audio (2)" in text and "- Note: x" in text
