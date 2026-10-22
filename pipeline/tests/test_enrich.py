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


# -- stage 40 additions (Phase 3) ----------------------------------------------------------

from karteikasten_pipeline.stages import enrich  # noqa: E402


def entry(**fields):
    return {"senses": [{"glosses": ["x"]}], **fields}


def test_case_evidence_puts_the_german_main_case_first():
    en = [entry(categories=["German prepositions governing the dative", "German prepositions governing the genitive"])]
    de = [{"senses": [{"tags": [], "raw_tags": ["Präposition mit Genitiv", "umgangssprachlich auch mit Dativ"]}]}]
    evidence = enrich.case_evidence(en, de)
    assert evidence.de_main == ["gen"] and evidence.de_secondary == ["dat"]
    assert evidence.cases() == ["gen", "dat"]
    assert evidence.agree()


def test_case_evidence_flags_editions_that_disagree():
    en = [entry(categories=["German prepositions governing the accusative",
                            "German prepositions governing the dative"])]
    de = [{"senses": [{"tags": ["with-dative"]}]}]
    evidence = enrich.case_evidence(en, de)
    assert evidence.cases() == ["dat", "acc"]
    assert not evidence.agree()


def test_german_tags_name_the_case_as_a_word():
    de = [{"senses": [{"tags": ["genitive prepositional", "with-dative"]}]}]
    assert enrich.case_evidence([], de).de_main == ["gen", "dat"]


def test_one_edition_alone_is_no_disagreement():
    de = [{"senses": [{"tags": ["with-accusative", "with-dative"]}]}]
    assert enrich.case_evidence([entry()], de).agree()


def test_two_way_needs_accusative_and_dative_as_the_main_cases():
    card = enrich.Card(id="vor#prep#1", lemma="vor", pos="prep")
    enrich.set_cases(card, ["dat", "acc"], "test")
    assert card.key_forms["case"] == "two-way"
    enrich.set_cases(card, ["gen", "dat", "acc"], "test")
    assert card.key_forms["case"] == "gen"


def test_conjunction_type_prefers_a_single_english_category():
    en = [entry(categories=["German coordinating conjunctions", "German subordinating conjunctions"])]
    de = [{"pos_title": "Subjunktion", "senses": [{"tags": []}]}]
    evidence = enrich.conjunction_evidence(en, de)
    assert evidence.kind() == "subordinating" and not evidence.agree()
    single = enrich.conjunction_evidence([entry(categories=["German coordinating conjunctions"])], de)
    assert single.kind() == "coordinating"


def test_case_table_by_gender_or_by_number():
    article = [{"forms": [
        {"form": "der", "tags": ["nominative", "singular", "masculine"]},
        {"form": "die", "tags": ["nominative", "singular", "feminine"]},
        {"form": "das", "tags": ["nominative", "singular", "neuter"]},
        {"form": "die", "tags": ["nominative", "plural"]},
        {"form": "d.", "tags": ["abbreviation"]},
    ]}]
    table = enrich.case_table(article)
    assert table["columns"] == ["m", "f", "n", "pl"]
    assert table["rows"][0]["cells"] == ["der", "die", "das", "die"]
    assert table["rows"][1]["cells"] == [None, None, None, None]
    pronoun = [{"forms": [{"form": "ich", "tags": ["nominative", "singular"]}, {"form": "wir", "tags": ["nominative", "plural"]}]}]
    assert enrich.case_table(pronoun)["columns"] == ["sg", "pl"]
    assert enrich.case_table([{"forms": []}]) is None


def test_ordinal_from_derived_terms_or_etymology():
    ordinals = {"zweite": "From zwei + -te. Displaced older ander.", "hundertste": "", "zweiteilig": ""}
    de = [{"derived": [{"word": "zweiteilig"}, {"word": "zweite"}]}]
    assert enrich.ordinal("zwei", [], de, ordinals) == "zweite"
    assert enrich.ordinal("zwei", [], [], ordinals) == "zweite"  # by its etymology alone
    assert enrich.ordinal("hundert", [{"derived": [{"word": "hundertste"}]}], [], ordinals) == "hundertste"
    assert enrich.ordinal("eins", [], [], ordinals) is None


def test_all_english_cognates_of_a_clause():
    entries = [{"etymology_text": "Compare Dutch twee, English two, twain, West Frisian twa."}]
    assert enrich.etymology_cognates(entries) == ["two", "twain"]


@pytest.mark.parametrize(
    ("etymology", "glosses", "hint"),
    [
        ("Compare English house.", ["house"], "house"),
        ("Compare English sheen.", ["already"], None),
        ("Cognate with English thank.", ["thanks; gratitude"], "thank"),  # plural folded
        ("Compare English two, twain.", ["two"], "two"),
    ],
)
def test_cognate_hint_only_when_glossed(etymology, glosses, hint):
    en = [{"etymology_text": etymology, "senses": [{"glosses": glosses}]}]
    card = enrich.build_card("x#noun#1", en, [], None)
    assert card.cognate_en == hint
    assert card.cognates_raw


def test_modals_get_their_own_class_and_wissen_is_mixed():
    def entry(word: str, *categories: str) -> list[dict]:
        return [{"head_templates": [{"expansion": f"{word} (preterite-present, third-person singular present kann)"}],
                 "categories": ["German preterite-present verbs", *categories],
                 "senses": [{"glosses": ["to be able"]}], "forms": []}]

    modal = enrich.build_card("können#verb#1", entry("können", "German modal verbs"), [], None)
    assert "modal" in modal.flags
    assert not {"strong", "weak", "mixed"} & set(modal.flags)
    wissen = enrich.build_card("wissen#verb#1", entry("wissen"), [], None)
    assert "mixed" in wissen.flags
    assert "modal" not in wissen.flags


def test_closed_classes_win_over_the_extracted_values():
    from karteikasten_pipeline.overrides import ClosedClasses

    card = enrich.Card(id="vor#prep#1", lemma="vor", pos="prep")
    enrich.set_cases(card, ["dat"], "extracted")
    closed = ClosedClasses(prepositions={"vor#prep#1": ["acc", "dat"]}, contractions={"vor#prep#1": ["vorm"]})
    enrich.apply_closed_classes(card, closed)
    assert card.key_forms["case"] == "two-way" and card.key_forms["contractions"] == ["vorm"]
    assert card.sources["case"].startswith("manual")


def test_plural_from_the_table_when_the_head_has_none():
    en = [{"senses": [{"glosses": ["heart"], "tags": ["neuter"]}], "forms": [
        {"form": "Herzen", "tags": ["definite", "nominative", "plural"]},
        {"form": "Herzen", "tags": ["dative", "definite", "plural"]},
    ]}]
    assert enrich.build_card("Herz#noun#1", en, [], None).key_forms["plural"] == "Herzen"
