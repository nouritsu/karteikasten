from pathlib import Path

import pytest

from karteikasten_pipeline.readers import conllu
from karteikasten_pipeline.stages import ud

EXCERPT = Path(__file__).parent / "fixtures" / "ud-gsd-excerpt.conllu"


def test_reader_yields_each_sentence_with_its_words():
    sentences = list(conllu.read(EXCERPT))
    assert len(sentences) == 3
    assert [w.form for w in sentences[0][:4]] == ["Das", "nächste", "mal", "rief"]


def test_contractions_are_one_token_split_into_words():
    words = next(s for s in conllu.read(EXCERPT) if any(w.token == "im" for w in s))
    im = [w for w in words if w.token == "im"]
    assert [(w.form, w.token_start) for w in im] == [("in", True), ("dem", False)]


def test_a_contraction_counts_once_under_its_surface_form():
    stats = ud.collect([EXCERPT])
    assert stats.for_token("im") == [("in", "ADP", "APPR", 1)]
    assert not any(token == "im" and lemma == "der" for token, lemma, _, _ in stats.analyses)


def test_separated_particle_verbs_are_reassembled():
    stats = ud.collect([EXCERPT])
    assert stats.split["anrufen"] == 1  # "rief ich extra vorher an"
    assert stats.unsplit["anrufen"] == 1  # "noch einmal anrufen"
    assert stats.unsplit["rufen"] >= 1  # the split use keeps the base lemma
    # "zurück gerufen", written apart in the source, is annotated as a split particle verb too.
    assert stats.split["zurückrufen"] == 1
    assert stats.split_heads["rufen"] == 2
    assert "anrufen" in stats.particle_verbs


def test_separated_particles_are_measured_by_their_stts_tag():
    stats = ud.collect([EXCERPT])
    assert ("an", "an", "ADP", "PTKVZ") in stats.analyses
    assert 0 < stats.separated_share("an") <= 1


def test_split_ratio_overall_and_shrunk_per_verb():
    stats = ud.UdStats()
    stats.split.update({"anrufen": 3, "aufhören": 1})
    stats.unsplit.update({"anrufen": 1, "aufhören": 3})
    assert stats.split_ratio() == pytest.approx(1.0)
    assert stats.split_ratio("anrufen", prior_weight=0) == pytest.approx(3.0)
    assert stats.split_ratio("anrufen", prior_weight=4) == pytest.approx((3 + 4) / (1 + 4))
