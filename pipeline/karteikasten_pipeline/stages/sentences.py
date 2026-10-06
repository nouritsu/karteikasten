"""Stage 60: example sentences per word.

Candidates are Tatoeba sentences (with their English translations) and Wiktionary
examples. A sentence matches a word when one of the word's forms appears as a
token; for a separable verb the separated stem must be followed by its particle
("Ich fange morgen an"). Kept: 4-10 tokens, not tagged as needing review.
Native authors (Tatoeba level 5) rank first. The app later shows the stored
sentence with the most words the learner already knows.
"""

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

TOKEN = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
# Tatoeba tags that mean the sentence is not settled yet (docs/sources/tatoeba.md).
REVIEW_TAGS = frozenset(
    {
        "@needs native check",
        "needs native check",
        "@check",
        "@change",
        "@delete",
        "delete",
        "unnatural",
        "wrong grammar",
        "@check translation",
        "check translation",
        "@change punctuation",
        "@change or unlink",
        "@change flag",
        "@check link",
        "@check links",
        "@check copyright",
    }
)
MIN_TOKENS, MAX_TOKENS = 4, 10
KEEP = 5
EMPTY: frozenset[str] = frozenset()


@dataclass
class Candidate:
    source: str  # "tatoeba" or "wiktionary"
    source_ref: str  # Tatoeba sentence id, or the Wiktionary entry
    de: str
    en: str | None
    author: str | None
    licence: str
    native: bool
    hl: tuple[int, int]  # character span of the matched form in `de`
    score: float = 0.0
    en_author: str | None = None
    en_licence: str | None = None


@dataclass
class WordForms:
    """What counts as an occurrence of one lemma in a sentence."""

    forms: set[str]
    stems: set[str] = field(default_factory=set)  # separated finite forms of a separable verb
    particle: str | None = None
    lemma: str = ""  # a sentence showing the headword itself teaches it best


def tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in TOKEN.finditer(text)]


def find(text: str, word: WordForms) -> tuple[int, int] | None:
    """Character span of the first occurrence of `word` in `text`, or None."""
    toks = tokens(text)
    for i, (token, start, end) in enumerate(toks):
        variants = {token, token.lower()} if i == 0 else {token}
        if variants & word.forms:
            return start, end
        if word.particle and variants & word.stems:
            if any(later == word.particle for later, _, _ in toks[i + 1 :]):
                return start, end
    return None


def score(candidate: Candidate, length: int, lemma: str = "") -> float:
    """Native author, an English translation, the headword itself and 6-8 tokens are best."""
    shown = candidate.de[candidate.hl[0] : candidate.hl[1]]
    return (
        (2.0 if candidate.native else 0.0)
        + (1.0 if candidate.en else 0.0)
        + (0.5 if lemma and shown.lower() == lemma.lower() else 0.0)
        - abs(length - 7) * 0.1
    )


def select(
    words: Mapping[str, WordForms],
    german: Iterable[tuple[int, str, str | None, str]],
    english: Mapping[int, tuple[str, str | None, str]],
    links: Mapping[int, list[int]],
    review: set[int],
    native_authors: set[str],
) -> dict[str, list[Candidate]]:
    """Best Tatoeba candidates per lemma id. `german` yields (id, text, author, licence)."""
    by_form: dict[str, set[str]] = defaultdict(set)
    for id_, word in words.items():
        for form in word.forms | word.stems:
            by_form[form].add(id_)
    found: dict[str, list[Candidate]] = defaultdict(list)
    for sentence_id, text, author, licence in german:
        if sentence_id in review:
            continue
        toks = tokens(text)
        if not MIN_TOKENS <= len(toks) <= MAX_TOKENS:
            continue
        hits = {id_ for token, _, _ in toks for id_ in by_form.get(token, EMPTY) | by_form.get(token.lower(), EMPTY)}
        for id_ in hits:
            span = find(text, words[id_])
            if span is None:
                continue
            translation = next((english[e] for e in links.get(sentence_id, []) if e in english), None)
            candidate = Candidate(
                source="tatoeba",
                source_ref=str(sentence_id),
                de=text,
                en=translation[0] if translation else None,
                author=author,
                licence=licence,
                native=author in native_authors,
                hl=span,
                en_author=translation[1] if translation else None,
                en_licence=translation[2] if translation else None,
            )
            candidate.score = score(candidate, len(toks), words[id_].lemma)
            found[id_].append(candidate)
    return {
        id_: sorted(cands, key=lambda c: (-c.score, int(c.source_ref)))[:KEEP] for id_, cands in found.items()
    }
