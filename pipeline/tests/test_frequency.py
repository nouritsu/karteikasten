from karteikasten_pipeline.stages import frequency
from karteikasten_pipeline.stages.lexicon import Lemma, Lexicon
from karteikasten_pipeline.stages.ud import UdStats


def lexicon():
    lemmas = {
        "okay#adj#1": Lemma("okay#adj#1", "okay", "adj", 1),
        "okay#intj#1": Lemma("okay#intj#1", "okay", "intj", 1),
        "Haus#noun#1": Lemma("Haus#noun#1", "Haus", "noun", 1),
    }
    candidates = {"okay": {"okay#adj#1", "okay#intj#1"}, "Haus": {"Haus#noun#1"}}
    return Lexicon(lemmas=lemmas, candidates=candidates, separable={}, german_words={"okay", "Haus"})


def rank(**kwargs):
    ud = UdStats()
    ud.index()
    spoken = {"okay": 300, "haus": 100}
    written = {"okay": (10, 0), "Haus": (300, 0)}
    return frequency.rank(spoken, written, lexicon(), ud, spoken_weight=0.7, epsilon=0.1, exclude={}, **kwargs)


def test_merge_moves_the_counts_onto_one_card():
    plain = {r.id: r for r in rank().ranked}
    merged = rank(merge={"okay#adj#1": "okay#intj#1"})
    by_id = {r.id: r for r in merged.ranked}
    assert "okay#adj#1" not in by_id and merged.dropped["okay#adj#1"] == "merged into okay#intj#1"
    assert by_id["okay#intj#1"].blended_pm > plain["okay#intj#1"].blended_pm
    assert "merged" in by_id["okay#intj#1"].flags
    assert abs(sum(r.token_share for r in merged.ranked) - sum(r.token_share for r in plain.values())) < 0.02
