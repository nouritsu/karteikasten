"""Stage 40: card content per word, taken from both Wiktionary editions.

Nothing here is invented: a field the data does not have stays empty and shows
up in the coverage report. Every field records which edition it came from.

- English edition: POS, gender, flags (weak noun, plural only, reflexive,
  strong/weak verb), key forms and English glosses, cognate from the etymology.
- German edition: German definitions, IPA (Germany standard), hyphenation,
  conjunction type (Subjunktion vs Konjunktion), case a preposition governs,
  noun declension tables with articles.
"""

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

from karteikasten_pipeline.stages.lexicon import NOT_CURRENT_TAGS

GENDERS = {"masculine": "m", "feminine": "f", "neuter": "n"}
ARTICLE = {"m": "der", "f": "die", "n": "das"}
REGISTER_TAGS = frozenset(
    {"colloquial", "informal", "vulgar", "slang", "derogatory", "offensive", "formal", "dated", "rare", "regional",
     "Austria", "Switzerland", "Southern-Germany", "Northern-Germany", "humorous", "euphemistic", "figuratively"}
)
CASES = ("nominative", "genitive", "dative", "accusative")
PERSONS = (
    ("ich", {"first-person", "singular"}),
    ("du", {"second-person", "singular"}),
    ("er/sie/es", {"third-person", "singular"}),
    ("wir", {"first-person", "plural"}),
    ("ihr", {"second-person", "plural"}),
    ("sie/Sie", {"third-person", "plural"}),
)
FUNCTION_POS = frozenset({"article", "det", "pron", "prep", "postp", "conj", "particle"})
# German edition POS for an English-edition POS.
DE_POS = {"article": {"det"}, "det": {"det", "pron"}, "postp": {"prep", "postp"}}
PARTICLE_TITLES = frozenset({"Modalpartikel", "Antwortpartikel", "Gradpartikel", "Fokuspartikel", "Partikel"})
INFLECTED_TITLES = frozenset({"Deklinierte Form", "Konjugierte Form", "Partizip I", "Partizip II", "Komparativ", "Superlativ"})
COGNATE = re.compile(
    r"(?:[Cc]ognate with|[Cc]ompare|[Aa]kin to|[Rr]elated to)\b[^.;]*?(?<!Old )(?<!Middle )\bEnglish ([A-Za-z][\w'-]*)"
)
FOOTNOTE = re.compile(r"\^\(\[[^\]]*\]\)|\[\d+[a-z]?\]")
IPA_VOWELS = set("aeiouyæøœɐɑɒɔəɛɜɪʊʏʌɯɨʉ")
IPA_STRESS = "\u02c8"
SYLLABIC = "\u0329"  # combining vertical line below: syllabic consonant (l̩, n̩)
VOWEL_MARKS = "\u0303"  # nasal: part of the vowel
# A non-syllabic glide (aɪ̯) or a length mark (uː) closes the vowel: a vowel right
# after it is the next syllable (freuen [ˈfʁɔɪ̯ən], ruhig [ˈʁuːɪç]).
NON_SYLLABIC = "\u032f"
ENDS_VOWEL = NON_SYLLABIC + "\u02d0\u02d1"


@dataclass
class Gloss:
    text: str
    tags: list[str] = field(default_factory=list)


@dataclass
class Card:
    id: str
    lemma: str
    pos: str
    gender: str | None = None
    article: str | None = None
    ipa: str | None = None
    syllables: list[str] | None = None
    stress_syllable: int | None = None
    cognate_en: str | None = None
    flags: list[str] = field(default_factory=list)
    key_forms: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, Any] = field(default_factory=dict)
    gloss_en: list[Gloss] = field(default_factory=list)
    gloss_de: list[Gloss] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)  # field -> where it came from
    issues: list[str] = field(default_factory=list)  # for the coverage report

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# -- helpers ------------------------------------------------------------------------------


def _senses(entries: Iterable[dict]) -> list[dict]:
    return [s for e in entries for s in e.get("senses", []) if "form_of" not in s and "alt_of" not in s]


def _current(senses: list[dict]) -> list[dict]:
    """Senses that are not archaic, obsolete, dated or dialectal (all of them if none are)."""
    current = [s for s in senses if not set(s.get("tags", [])) & NOT_CURRENT_TAGS]
    return current or senses


def _forms(entries: Iterable[dict], *required: str, exclude: Iterable[str] = ()) -> list[str]:
    """Forms carrying all `required` tags and none of `exclude`, in source order, deduplicated."""
    need, avoid = set(required), set(exclude) | {"table-tags", "inflection-template", "error-unrecognized-form"}
    seen: list[str] = []
    for entry in entries:
        for form in entry.get("forms", []):
            tags = set(form.get("tags", []))
            if need <= tags and not tags & avoid and form["form"] not in seen:
                seen.append(form["form"])
    return seen


def gloss_text(sense: dict) -> str:
    glosses = sense.get("glosses", [])
    return FOOTNOTE.sub("", glosses[-1]).strip() if glosses else ""


def ipa_nuclei(ipa: str) -> list[int]:
    """Positions of syllable nuclei: a run of vowels (a diphthong) or a syllabic consonant."""
    nuclei, in_vowel = [], False
    for i, ch in enumerate(ipa):
        if ch in IPA_VOWELS:
            if not in_vowel:
                nuclei.append(i)
            in_vowel = True
        elif ch == SYLLABIC and i > 0:
            nuclei.append(i - 1)
            in_vowel = False
        elif ch in ENDS_VOWEL:
            if ch == NON_SYLLABIC and nuclei and nuclei[-1] == i - 1:
                nuclei.pop()  # a lone non-syllabic vowel is a glide (Familie [faˈmiːli̯ə])
            in_vowel = False
        elif ch in VOWEL_MARKS:
            continue
        else:
            in_vowel = False
    return sorted(set(nuclei))


def stressed_syllable(ipa: str) -> tuple[int, int]:
    """(index of the stressed syllable, number of syllables) read from the IPA."""
    nuclei = ipa_nuclei(ipa)
    mark = ipa.find(IPA_STRESS)
    if mark < 0:
        return 0, len(nuclei)
    return sum(1 for n in nuclei if n < mark), len(nuclei)


# -- per word type --------------------------------------------------------------------------


def noun(card: Card, en: list[dict], de: list[dict]) -> None:
    senses = _current(_senses(en))
    tags = [t for s in senses[:3] for t in s.get("tags", [])]
    genders = [GENDERS[t] for t in tags if t in GENDERS]
    if "plural-only" in tags:
        card.flags.append("plural_only")
        card.article = "die"
    elif genders:
        card.gender = genders[0]
        card.article = ARTICLE[genders[0]]
    if card.gender or card.article:
        card.sources["gender"] = "kaikki-en"
    if "weak" in tags:
        card.flags.append("weak_noun")
    if {"no-plural", "singular-only", "uncountable"} & set(tags) and "plural-only" not in tags:
        card.flags.append("singular_only")
    plurals = _forms(en, "plural", exclude=("diminutive", "genitive", "dative", "accusative", "definite"))
    genitives = _forms(en, "genitive", exclude=("plural", "diminutive", "definite", "indefinite"))
    if plurals and "plural_only" not in card.flags:
        card.key_forms["plural"] = plurals[0]
        card.key_forms["plural_alt"] = plurals[1:3]
    if genitives:
        card.key_forms["genitive"] = genitives[0]
    if card.key_forms:
        card.sources["key_forms"] = "kaikki-en"
    table = {}
    for entry in de:
        for form in entry.get("forms", []):
            ftags = set(form.get("tags", []))
            case = next((c for c in CASES if c in ftags), None)
            number = "plural" if "plural" in ftags else "singular" if "singular" in ftags else None
            if case and number and (case, number) not in table:
                table[(case, number)] = {"form": form["form"], "article": form.get("article")}
    if table:
        card.tables["declension"] = [
            {"case": case, **{number: table.get((case, number)) for number in ("singular", "plural")}} for case in CASES
        ]
        card.sources["tables"] = "kaikki-de"


def _stem_changes(infinitive: str, du_form: str) -> bool:
    stem = infinitive.split(" ")[0]
    for ending in ("eln", "ern", "en", "n"):
        if stem.endswith(ending):
            stem = stem[: -len(ending)] if ending in ("en", "n") else stem[:-1]
            break
    first = du_form.split(" ")[0]
    return not (first.startswith(stem) or first.startswith(stem + "e"))


def verb(card: Card, en: list[dict], separable: str | None) -> None:
    senses = _current(_senses(en))
    tags = {t for s in senses for t in s.get("tags", [])}
    main_tags = {t for s in senses[:3] for t in s.get("tags", [])}
    if separable:
        card.flags.append("separable")
        card.key_forms["particle"] = separable
    if "reflexive" in main_tags:
        card.flags.append("reflexive")
    head = " ".join(h.get("expansion", "") for e in en for h in e.get("head_templates", []))
    if "strong" in tags or " strong" in head:
        card.flags.append("strong")
    elif "irregular" in tags or "mixed" in tags or "irregular" in head:
        card.flags.append("mixed")
    elif "weak" in tags or " weak" in head:
        card.flags.append("weak")

    def one(*required: str, exclude: Iterable[str] = ()) -> str | None:
        found = _forms(en, *required, exclude=exclude)
        return found[0] if found else None

    er = one("third-person", "singular", "present", "indicative", exclude=("subordinate-clause",)) or one(
        "third-person", "singular", "present", exclude=("subjunctive", "subjunctive-i", "subordinate-clause")
    )
    du = one("second-person", "singular", "present", "indicative", exclude=("subordinate-clause",))
    past = one("third-person", "singular", "preterite", "indicative", exclude=("subordinate-clause",)) or one(
        "past", exclude=("participle",)
    )
    participle = one("participle", "past")
    auxiliaries = [
        f for f in _forms(en, "auxiliary", exclude=("colloquial", "regional", "Northwest-German", "dialectal"))
        if f in ("haben", "sein")
    ]
    for key, value in (("er", er), ("praeteritum", past), ("partizip2", participle)):
        if value:
            card.key_forms[key] = value
    if du and _stem_changes(card.lemma, du):
        card.key_forms["du"] = du
    if auxiliaries:
        card.key_forms["auxiliary"] = auxiliaries
    if card.key_forms:
        card.sources["key_forms"] = "kaikki-en"

    def conjugation(*mood: str) -> list[dict]:
        rows = []
        for person, ptags in PERSONS:
            forms = _forms(en, *mood, *ptags, exclude=("subordinate-clause", "rare"))
            rows.append({"person": person, "form": forms[0] if forms else None})
        return rows

    present = conjugation("present", "indicative")
    if any(row["form"] for row in present):
        card.tables["present"] = present
        card.tables["preterite"] = conjugation("preterite", "indicative")
        card.tables["imperative"] = [
            {"person": person, "form": (_forms(en, "imperative", *ptags) or [None])[0]}
            for person, ptags in (("du", {"second-person", "singular"}), ("ihr", {"second-person", "plural"}))
        ]
        if card.lemma in ("haben", "sein", "werden") or "modal" in tags or "auxiliary" in tags:
            card.tables["subjunctive_ii"] = conjugation("subjunctive-ii")
        card.sources["tables"] = "kaikki-en"


def adjective(card: Card, en: list[dict]) -> None:
    comparative = _forms(en, "comparative", exclude=("strong", "weak", "mixed"))
    superlative = _forms(en, "superlative", exclude=("strong", "weak", "mixed"))
    if comparative:
        card.key_forms["comparative"] = comparative[0]
    if superlative:
        card.key_forms["superlative"] = superlative[0]
    attributive = _forms(en, "strong", "nominative", "masculine", "singular", exclude=("comparative", "superlative"))
    if attributive and attributive[0].endswith("er"):
        stem = attributive[0][:-2]
        if stem != card.lemma and not card.lemma.startswith(stem):
            card.flags.append("irregular_stem")
            card.key_forms["attributive"] = stem + "e"
    tags = {t for s in _current(_senses(en))[:3] for t in s.get("tags", [])}
    if "predicative" in tags and not attributive:
        card.flags.append("predicative_only")
    if card.key_forms:
        card.sources["key_forms"] = "kaikki-en"


def adverb(card: Card, en: list[dict]) -> None:
    comparative, superlative = _forms(en, "comparative"), _forms(en, "superlative")
    if comparative and superlative:
        card.key_forms["comparative"] = comparative[0]
        card.key_forms["superlative"] = superlative[0]
        card.sources["key_forms"] = "kaikki-en"


def preposition(card: Card, de: list[dict]) -> None:
    tags = {t for e in de for s in e.get("senses", []) for t in s.get("tags", [])}
    raw = " ".join(t for e in de for s in e.get("senses", []) for t in s.get("raw_tags", []))
    found = {}
    for case, tag, word in (("acc", "with-accusative", "Akkusativ"), ("dat", "with-dative", "Dativ"),
                            ("gen", "with-genitive", "Genitiv")):
        if tag in tags:
            found[case] = -1
        elif word in raw:
            found[case] = raw.index(word)
    cases = sorted(found, key=found.get)  # tagged cases first, then in the order the text names them
    if cases:
        card.key_forms["case"] = "two-way" if set(cases) >= {"acc", "dat"} else cases[0]
        card.key_forms["cases"] = cases
        card.sources["key_forms"] = "kaikki-de (unchecked; closed_classes.toml decides)"


def conjunction(card: Card, de: list[dict]) -> None:
    kinds = []
    for entry in de:
        current = [s for s in entry.get("senses", []) if not set(s.get("tags", [])) & (NOT_CURRENT_TAGS | {"colloquial"})]
        if current and entry.get("pos_title") == "Subjunktion":
            kinds.append("subordinating")
        elif current and entry.get("pos_title") == "Konjunktion":
            kinds.append("coordinating")
    if kinds:
        card.key_forms["conjunction"] = kinds[0]
        card.sources["key_forms"] = "kaikki-de"


# -- the card -------------------------------------------------------------------------------


def german_entries_for(card: Card, de_all: list[dict]) -> list[dict]:
    wanted = DE_POS.get(card.pos, {card.pos})
    return [e for e in de_all if e.get("pos") in wanted and e.get("pos_title") not in INFLECTED_TITLES]


def build_card(lemma_id: str, en: list[dict], de_all: list[dict], separable: str | None) -> Card:
    word, pos, _ = lemma_id.split("#")
    card = Card(id=lemma_id, lemma=word, pos=pos)
    de = german_entries_for(card, de_all)

    senses = _current(_senses(en))
    for sense in senses:
        text = gloss_text(sense)
        if text and len(card.gloss_en) < 3 and all(g.text != text for g in card.gloss_en):
            card.gloss_en.append(Gloss(text, sorted(set(sense.get("tags", [])) & REGISTER_TAGS)))
    if card.gloss_en:
        card.sources["gloss_en"] = "kaikki-en"
    for entry in de:
        for sense in _current(entry.get("senses", [])):
            text = gloss_text(sense)
            if text and len(card.gloss_de) < 3 and all(g.text != text for g in card.gloss_de):
                card.gloss_de.append(Gloss(text, sorted(set(sense.get("tags", [])) & REGISTER_TAGS)))
    if card.gloss_de:
        card.sources["gloss_de"] = "kaikki-de"
    if any("vulgar" in s.get("tags", []) for s in senses[:3]):
        card.flags.append("vulgar")

    de_ipa = [s["ipa"] for e in (de or de_all) for s in e.get("sounds", []) if s.get("ipa")]
    en_ipa = [s["ipa"] for e in en for s in e.get("sounds", []) if s.get("ipa") and not set(s.get("tags", [])) - {"Germany"}]
    if de_ipa:
        card.ipa, card.sources["ipa"] = de_ipa[0], "kaikki-de"
    elif en_ipa:
        card.ipa, card.sources["ipa"] = en_ipa[0], "kaikki-en"
    parts = next((h["parts"] for e in (de or de_all) for h in e.get("hyphenations", []) if h.get("parts")), None)
    if parts:
        card.syllables, card.sources["syllables"] = parts, "kaikki-de"
    if card.ipa and card.syllables:
        index, count = stressed_syllable(card.ipa)
        if count == len(card.syllables):
            card.stress_syllable = index
        else:
            card.issues.append(f"syllables: {len(card.syllables)} in hyphenation, {count} in IPA")

    for entry in en:
        if match := COGNATE.search(entry.get("etymology_text", "") or ""):
            card.cognate_en, card.sources["cognate_en"] = match.group(1), "kaikki-en etymology"
            break

    if pos == "noun":
        noun(card, en, de)
    elif pos == "verb":
        verb(card, en, separable)
    elif pos == "adj":
        adjective(card, en)
    elif pos == "adv":
        adverb(card, en)
    elif pos in ("prep", "postp"):
        preposition(card, de)
    elif pos == "conj":
        conjunction(card, de)
    if "comparative" not in card.key_forms:
        # Comparison filed under another POS: viel (determiner) -> mehr -> am meisten.
        comparative, superlative = _forms(en, "comparative"), _forms(en, "superlative")
        if comparative and superlative:
            card.key_forms.update(comparative=comparative[0], superlative=superlative[0])
            card.sources.setdefault("key_forms", "kaikki-en")
    if pos in FUNCTION_POS:
        card.flags.append("function_word")
    # German Wiktionary files the particle uses separately (doch, mal, ja); the English
    # edition often puts the card under conjunction or adverb.
    particle_use = any(e.get("pos_title") in PARTICLE_TITLES for e in de_all)
    if pos in ("particle", "intj") or particle_use:
        card.flags.append("context_dependent")
        if particle_use:
            card.sources["context_dependent"] = "kaikki-de pos_title"
    return card
