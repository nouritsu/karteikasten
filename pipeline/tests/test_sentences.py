from karteikasten_pipeline.stages import sentences
from karteikasten_pipeline.stages.sentences import Candidate, WordForms

HAND = WordForms(forms={"Hand", "Hände"}, lemma="Hand")


def german(*texts):
    return [(i, text, "anna", "CC BY 2.0 FR") for i, text in enumerate(texts, start=1)]


def test_keeps_the_best_candidates_and_any_pinned_sentence():
    numbers = [str(n) for n in range(sentences.CANDIDATES + 2)]
    texts = [f"Das ist meine Hand Nummer {'x' * (int(n) + 1)}." for n in numbers]
    texts.append("Gib mir bitte deine Hand.")  # the only one with an English translation
    rows = german(*texts)
    english = {100: ("Please give me your hand.", "bob", "CC BY 2.0 FR")}
    last = len(rows)
    best, pinned, _ = sentences.select({"Hand#noun#1": HAND}, rows, english, {last: [100]}, set(), {"anna"},
                                       pins={"Hand#noun#1": ["tatoeba:7"]})
    kept = best["Hand#noun#1"]
    assert len(kept) == sentences.CANDIDATES
    assert kept[0].source_ref == str(last) and kept[0].en == "Please give me your hand."
    assert "tatoeba:7" not in {c.id for c in kept} and set(pinned["Hand#noun#1"]) == {"tatoeba:7"}
    assert len(sentences.final(kept, [], [], set())) == sentences.KEEP


def test_sentences_and_translations_need_an_author():
    rows = [(1, "Gib mir deine Hand bitte.", None, "CC BY 2.0 FR"), (2, "Das ist meine Hand hier.", "anna", "CC0 1.0")]
    english = {100: ("That is my hand here.", None, "CC BY 2.0 FR")}
    best, _, _ = sentences.select({"Hand#noun#1": HAND}, rows, english, {2: [100]}, set(), set())
    assert [c.source_ref for c in best["Hand#noun#1"]] == ["2"]
    assert best["Hand#noun#1"][0].en is None


def test_bans_are_skipped_and_reported():
    rows = german("Gib mir deine Hand bitte.", "Das ist meine Hand hier.")
    best, _, used = sentences.select({"Hand#noun#1": HAND}, rows, {}, {}, set(), set(),
                                     bans={"Hand#noun#1": ["tatoeba:1"]})
    assert [c.id for c in best["Hand#noun#1"]] == ["tatoeba:2"]
    assert used == {("Hand#noun#1", "tatoeba:1")}


def test_wiktionary_examples_but_not_quotations():
    entries = [{"senses": [{"examples": [
        {"type": "example", "text": "Ich gebe dir die Hand.", "english": "I give you my hand."},
        {"type": "quotation", "text": "Er nahm sie bei der Hand.", "ref": "1900, Someone"},
        {"type": "example", "text": "Hand!"},
    ]}]}]
    found = sentences.wiktionary_examples(HAND, entries)
    assert [c.de for c in found] == ["Ich gebe dir die Hand."]
    assert found[0].author == sentences.WIKTIONARY_AUTHOR and found[0].en_author == sentences.WIKTIONARY_AUTHOR
    assert found[0].id.startswith("wiktionary:")


def test_final_puts_pins_first_and_drops_bans():
    def c(ref, score):
        return Candidate("tatoeba", ref, "x", None, "a", "l", False, (0, 1), score)

    tatoeba = [c("1", 3.0), c("2", 2.0), c("3", 1.0)]
    out = sentences.final(tatoeba, [], [c("9", 0.0)], {"tatoeba:1"})
    assert [x.source_ref for x in out] == ["9", "2", "3"]
