"""Stage 20: the German lexicon, from both Wiktionary editions via Kaikki.

The English edition supplies lemmas, POS, etymology numbers and forms; the
German edition confirms that a word exists in German Wiktionary. Full entries
are only read again for the words that make the deck, through the byte-offset
indexes `load` builds in the same pass, so the lexicon itself stays small.

Rules learned from the data (docs/sources/kaikki.md):
- entries sharing (word, pos, etymology) are one lemma (Hand also has a separate
  "clipping of Handspiel" entry);
- `forms` rows tagged table-tags, inflection-template, class or auxiliary are
  template debris ("haben" is not a form of anfangen); diminutives are other words;
- personal pronoun entries list the whole paradigm (ich, du, er, ...) as forms,
  tagged "personal"; those rows never count;
- proper nouns list their article as a "canonical" form ("die" for CIA), and a
  form spelled with another initial case than its lemma is another word;
- misspelling entries ("sie" as a misspelling of "Sie") are not lemmas, and
  obsolete spellings ("das" for "dass") do not count as forms;
- a contraction such as "im" counts toward its preposition.
"""

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from karteikasten_pipeline.readers import kaikki

DEBRIS_TAGS = frozenset(
    {
        "table-tags",
        "inflection-template",
        "class",
        "auxiliary",
        "error-unrecognized-form",
        "romanization",
        "canonical",
    }
)
OTHER_WORD_TAGS = frozenset({"diminutive", "augmentative", "abbreviation", "personal"})
OUTDATED_TAGS = frozenset({"obsolete", "archaic", "dated", "misspelling"})
# A lemma whose every sense carries one of these yields to a current homograph
# when UD cannot tell them apart (UD lemmatises "Leute" as archaic "Leut").
NOT_CURRENT_TAGS = frozenset({"obsolete", "archaic", "dated", "dialectal"})
# Word types whose forms Wiktionary files under one another (viele: adj form of det viel).
MODIFIERS = frozenset({"adj", "adv", "det", "pron", "num", "article", "particle"})
ARTICLES = frozenset({"der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer", "eines"})
# "contraction of an (“at/on”) + dem (“the”, ...)": the first word is the preposition.
# One level of nested parentheses: "an (“on(to)”) + das".
CONTRACTION = re.compile(r"^contraction of (\w+)(?: \((?:[^()]|\([^()]*\))*\))? \+ (\w+)")
# German separable particles, used to recognise "fängt an" as a form of "anfangen".
SEPARABLE_FORM = re.compile(r"^\S+ (\S+)$")


@dataclass(frozen=True, slots=True)
class Lemma:
    id: str
    word: str
    pos: str
    etym: int
    current: bool = True  # False when every sense is archaic, obsolete, dated or dialectal


@dataclass
class Lexicon:
    lemmas: dict[str, Lemma]
    candidates: dict[str, set[str]]  # surface token -> ids of lemmas it can be a form of
    separable: dict[str, str]  # particle verb id -> its particle ("anfangen#verb#1" -> "an")
    german_words: set[str] = field(default_factory=set)  # words with a German-edition entry
    contractions: dict[str, list[str]] = field(default_factory=dict)  # preposition id -> im, ins (not colloquial)
    ordinals: dict[str, str] = field(default_factory=dict)  # ordinal word -> its etymology text

    def in_german_wiktionary(self, word: str) -> bool:
        return word in self.german_words


def lemma_id(word: str, pos: str, etym: int) -> str:
    return f"{word}#{pos}#{etym}"


def entry_id(entry: dict) -> str:
    return lemma_id(entry["word"], entry["pos"], int(entry.get("etymology_number") or 1))


def _sense_kinds(entry: dict) -> set[str]:
    kinds = set()
    for sense in entry.get("senses", []):
        tags = sense.get("tags", [])
        if "misspelling" in tags:
            kinds.add("misspelling")
        elif "form_of" in sense or "form-of" in tags:
            kinds.add("form-of")
        elif "alt_of" in sense and "alt-of" in tags and "abbreviation" not in tags:
            kinds.add("alt-of")
        else:
            kinds.add("lemma")
    return kinds


def token_forms(word: str, pos: str, forms: list[dict]) -> Iterable[str]:
    """Single-token inflected forms, the headword included."""
    yield word
    for form in forms:
        tags = set(form.get("tags", []))
        text = form.get("form", "")
        if not text or " " in text or text.startswith("-"):
            continue
        if tags & (DEBRIS_TAGS | OTHER_WORD_TAGS):
            continue
        if "alternative" in tags and tags & OUTDATED_TAGS:
            continue
        if pos in ("noun", "name") and text in ARTICLES:
            continue
        # Capitalisation is part of the word: archaic "Er" lists "er", which is another word.
        if text[0].isupper() != word[0].isupper():
            continue
        yield text


def _separable_particle(word: str, forms: list[dict]) -> str | None:
    for form in forms:
        match = SEPARABLE_FORM.match(form.get("form", ""))
        if match and word.startswith(match.group(1)) and len(match.group(1)) < len(word):
            return match.group(1)
    return None


def _is_current(entry: dict) -> bool:
    return any(not set(sense.get("tags", [])) & NOT_CURRENT_TAGS for sense in entry.get("senses", []))


def build(en_entries: Iterable[dict], german_words: Iterable[str]) -> Lexicon:
    lemmas: dict[str, Lemma] = {}
    candidates: dict[str, set[str]] = defaultdict(set)
    separable: dict[str, str] = {}
    # (form word, pos, target word) for form-of and alt-of entries, resolved at the end
    links: list[tuple[str, str, str]] = []
    contractions: list[tuple[str, str]] = []  # (contraction id, preposition word)
    colloquial: set[str] = set()  # contraction ids Wiktionary tags colloquial (mim, fürn): counted, not listed

    ordinals: dict[str, str] = {}

    for entry in en_entries:
        if any("ordinal" in sense.get("tags", []) for sense in entry.get("senses", [])):
            ordinals.setdefault(entry["word"], entry.get("etymology_text") or "")
        kinds = _sense_kinds(entry)
        if kinds <= {"misspelling"}:
            continue
        if "lemma" not in kinds:
            for sense in entry.get("senses", []):
                if set(sense.get("tags", [])) & OUTDATED_TAGS:
                    continue
                for target in sense.get("form_of", []) + sense.get("alt_of", []):
                    links.append((entry["word"], entry["pos"], target["word"]))
            continue
        lemma = Lemma(
            entry_id(entry), entry["word"], entry["pos"], int(entry.get("etymology_number") or 1), _is_current(entry)
        )
        known = lemmas.get(lemma.id)
        if known is None or (lemma.current and not known.current):
            lemmas[lemma.id] = lemma
        forms = entry.get("forms", [])
        for form in token_forms(lemma.word, lemma.pos, forms):
            candidates[form].add(lemma.id)
        if lemma.pos == "verb" and (particle := _separable_particle(lemma.word, forms)):
            separable[lemma.id] = particle
        if lemma.pos == "contraction":
            # The first sense is the common one: "am" is an + dem far more often than auf + dem.
            for sense in entry.get("senses", [])[:1]:
                if match := CONTRACTION.match(" ".join(sense.get("glosses", []))):
                    contractions.append((lemma.id, match.group(1)))
                    if set(sense.get("tags", [])) & {"colloquial", "informal", "dialectal"}:
                        colloquial.add(lemma.id)

    by_word_pos: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_word: dict[str, list[str]] = defaultdict(list)
    for lemma in sorted(lemmas.values(), key=lambda lemma: lemma.id):
        by_word_pos[(lemma.word, lemma.pos)].append(lemma.id)
        by_word[lemma.word].append(lemma.id)
    listed = {form: set(ids) for form, ids in candidates.items()}
    for word, pos, target in links:
        # The target lemma under the same POS; else, among modifiers, the same word
        # under another POS ("viele" is filed as an adjective form of the determiner
        # "viel"; but the noun "Fahren" is not a form of the verb); else the
        # target is itself a form ("dies" -> "dieses" -> "dieser", "wär" -> "wäre" -> "sein").
        homographs = by_word_pos.get((target, pos), [])
        if not homographs and target in by_word:
            homographs = by_word[target] if pos in MODIFIERS else []
        elif not homographs:
            homographs = sorted(listed.get(target, ()))
        # Bänke is a form of Bank only in the etymology whose table lists it.
        chosen = [id_ for id_ in homographs if id_ in listed.get(word, ())] or homographs
        if chosen:
            candidates[word].update(chosen)

    # A contraction counts toward its preposition wherever it is a candidate ("ins" is
    # also listed in the table of "im"); other readings stay ("am" before a superlative).
    preposition_of = {
        contraction: lemma_id(preposition, "prep", 1)
        for contraction, preposition in contractions
        if lemma_id(preposition, "prep", 1) in lemmas and lemmas[contraction].word != preposition
    }
    for form, ids in candidates.items():
        if ids & preposition_of.keys():
            candidates[form] = {preposition_of.get(id_, id_) for id_ in ids}

    by_preposition: dict[str, set[str]] = defaultdict(set)
    for contraction, preposition in preposition_of.items():
        if contraction not in colloquial:
            by_preposition[preposition].add(lemmas[contraction].word)

    return Lexicon(
        lemmas=lemmas,
        candidates=dict(candidates),
        separable=separable,
        german_words=set(german_words),
        contractions={id_: sorted(words) for id_, words in sorted(by_preposition.items())},
        ordinals=ordinals,
    )


def load(work: Path) -> tuple[Lexicon, kaikki.Index, kaikki.Index]:
    """The lexicon, plus indexes into both extracts: English entries by lemma id,
    German entries by word. One pass over each file."""
    en_path, de_path = work / "kaikki" / "en.jsonl", work / "kaikki" / "de.jsonl"
    en_offsets: dict[str, list[int]] = defaultdict(list)
    de_offsets: dict[str, list[int]] = defaultdict(list)

    def en_entries() -> Iterable[dict]:
        for offset, entry in kaikki.read_with_offsets(en_path):
            en_offsets[entry_id(entry)].append(offset)
            yield entry

    def german_words() -> Iterable[str]:
        for offset, entry in kaikki.read_with_offsets(de_path):
            de_offsets[entry["word"]].append(offset)
            yield entry["word"]

    lexicon = build(en_entries(), german_words())
    return lexicon, kaikki.Index(en_path, dict(en_offsets)), kaikki.Index(de_path, dict(de_offsets))
