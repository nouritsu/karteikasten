import pytest

from karteikasten_pipeline.stages.enrich import COGNATE, stressed_syllable

# IPA strings as German Wiktionary gives them.


@pytest.mark.parametrize(
    ("ipa", "stressed", "syllables"),
    [
        ("[hant]", 0, 1),
        ("[ˈtaːfl̩]", 0, 2),  # syllabic l
        ("[t͡saɪ̯t]", 0, 1),  # affricate and diphthong
        ("[ˈanˌfaŋən]", 0, 3),  # secondary stress
        ("[eleˈfant]", 2, 3),
        ("[ˈfʁɔɪ̯ən]", 0, 2),  # a vowel after a diphthong starts a syllable
        ("[ˈʁuːɪç]", 0, 2),  # and so does one after a long vowel
        ("[faˈmiːli̯ə]", 1, 3),  # i̯ is a glide, not a syllable
        ("[ˈaːbn̩t]", 0, 2),
    ],
)
def test_stress_and_syllables_from_ipa(ipa, stressed, syllables):
    assert stressed_syllable(ipa) == (stressed, syllables)


@pytest.mark.parametrize(
    ("etymology", "cognate"),
    [
        ("From Middle High German hant, from Old High German hant. Compare Dutch hand, English hand, West Frisian hân.", "hand"),
        ("From Old High German hēr. Compare Old English hār.", None),  # Old English is not a hint
        ("Cognate with Middle English yernen and English yearn.", "yearn"),
    ],
)
def test_cognates_are_modern_english(etymology, cognate):
    match = COGNATE.search(etymology)
    assert (match.group(1) if match else None) == cognate


@pytest.mark.parametrize(
    ("gloss", "preposition"),
    [
        ("contraction of an (“on(to)”) + das (“the”)", "an"),
        ("contraction of in (“(in)to”) + das (“the”) (accusative singular neuter)", "in"),
        ("contraction of zu + der, literally “to the (feminine)”", "zu"),
    ],
)
def test_contraction_glosses_name_their_preposition(gloss, preposition):
    from karteikasten_pipeline.stages.lexicon import CONTRACTION

    assert CONTRACTION.match(gloss).group(1) == preposition
