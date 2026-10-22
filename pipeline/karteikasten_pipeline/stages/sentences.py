"""Stage 60: example sentences per word.

Candidates are Tatoeba sentences (with their English translations) and Wiktionary
usage examples (not quotations, which cite outside works). A sentence matches a
word when one of the word's forms appears as a token; for a separable verb the
separated stem must be followed by its particle ("Ich fange morgen an"). Kept:
4-10 tokens, not tagged as needing review, with a named author (a translation
without one is left out). Native authors (Tatoeba level 5) rank first. Pinned
sentences from overrides/sentences.toml come first, banned ones never. The app
later shows the stored sentence with the most words the learner already knows.
"""

import hashlib
import heapq
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
KEEP = 5  # sentences per word in the deck
CANDIDATES = 20  # best candidates per word kept for the curation tool's picker
EMPTY: frozenset[str] = frozenset()
WIKTIONARY_AUTHOR = "Wiktionary contributors"
WIKTIONARY_LICENCE = "CC BY-SA 4.0"


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

    @property
    def id(self) -> str:
        return f"{self.source}:{self.source_ref}"

    def order(self) -> tuple:
        """Best first: score, then Tatoeba before Wiktionary, then the older sentence."""
        tatoeba = self.source == "tatoeba"
        return (-self.score, not tatoeba, int(self.source_ref) if tatoeba else 0, self.source_ref)


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


class _Best:
    """The best CANDIDATES candidates of one word, plus any pinned ones."""

    def __init__(self, pinned: Iterable[str]):
        self.heap: list[tuple[_Inverted, int, Candidate]] = []  # the worst kept candidate on top
        self.pinned_ids = set(pinned)
        self.pinned: dict[str, Candidate] = {}
        self.count = 0

    def add(self, candidate: Candidate) -> None:
        if candidate.id in self.pinned_ids:
            self.pinned[candidate.id] = candidate
            return
        # heapq is a min-heap: with the order inverted, its top is the worst kept
        # candidate, replaced whenever a better one arrives.
        self.count += 1
        item = (_Inverted(candidate.order()), self.count, candidate)
        if len(self.heap) < CANDIDATES:
            heapq.heappush(self.heap, item)
        elif item[0] > self.heap[0][0]:
            heapq.heapreplace(self.heap, item)

    def best(self) -> list[Candidate]:
        return sorted((c for _, _, c in self.heap), key=Candidate.order)


class _Inverted:
    """Orders the reverse of the wrapped tuple, so the heap's smallest is the worst candidate."""

    __slots__ = ("key",)

    def __init__(self, key: tuple):
        self.key = key

    def __lt__(self, other: "_Inverted") -> bool:
        return self.key > other.key

    def __gt__(self, other: "_Inverted") -> bool:
        return self.key < other.key

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Inverted) and self.key == other.key


def select(
    words: Mapping[str, WordForms],
    german: Iterable[tuple[int, str, str | None, str]],
    english: Mapping[int, tuple[str, str | None, str]],
    links: Mapping[int, list[int]],
    review: set[int],
    native_authors: set[str],
    *,
    pins: Mapping[str, list[str]] | None = None,
    bans: Mapping[str, list[str]] | None = None,
) -> tuple[dict[str, list[Candidate]], dict[str, dict[str, Candidate]], set[tuple[str, str]]]:
    """The best CANDIDATES Tatoeba candidates per lemma id, the pinned candidates found per id, and
    the (word id, sentence id) bans that matched a candidate. `german` yields
    (id, text, author, licence); sentences without an author are skipped, and only
    translations with an author count."""
    pins, bans = pins or {}, bans or {}
    banned = {(id_, sentence) for id_, sentences in bans.items() for sentence in sentences}
    used_bans: set[tuple[str, str]] = set()
    by_form: dict[str, set[str]] = defaultdict(set)
    for id_, word in words.items():
        for form in word.forms | word.stems:
            by_form[form].add(id_)
    best = {id_: _Best(pins.get(id_, ())) for id_ in words}
    for sentence_id, text, author, licence in german:
        if sentence_id in review or not author:
            continue
        toks = tokens(text)
        if not MIN_TOKENS <= len(toks) <= MAX_TOKENS:
            continue
        hits = {id_ for token, _, _ in toks for id_ in by_form.get(token, EMPTY) | by_form.get(token.lower(), EMPTY)}
        if not hits:
            continue
        translation = next(
            (english[e] for e in sorted(links.get(sentence_id, [])) if e in english and english[e][1]), None
        )
        for id_ in sorted(hits):
            if (id_, f"tatoeba:{sentence_id}") in banned:
                used_bans.add((id_, f"tatoeba:{sentence_id}"))
                continue
            span = find(text, words[id_])
            if span is None:
                continue
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
            best[id_].add(candidate)
    chosen = {id_: b.best() for id_, b in best.items() if b.heap}
    pinned = {id_: b.pinned for id_, b in best.items() if b.pinned}
    return chosen, pinned, used_bans


def wiktionary_examples(word: WordForms, entries: Iterable[dict]) -> list[Candidate]:
    """Usage examples from the English edition's senses: type "example" only (a
    quotation cites an outside work), 4-10 tokens, containing the word."""
    found: dict[str, Candidate] = {}
    for entry in entries:
        for sense in entry.get("senses", []):
            for example in sense.get("examples", []):
                text = (example.get("text") or "").strip()
                if example.get("type") != "example" or example.get("ref") or not text:
                    continue
                toks = tokens(text)
                if not MIN_TOKENS <= len(toks) <= MAX_TOKENS or (span := find(text, word)) is None:
                    continue
                english = (example.get("english") or example.get("translation") or "").strip() or None
                ref = hashlib.sha1(text.encode()).hexdigest()[:12]
                candidate = Candidate(
                    source="wiktionary",
                    source_ref=ref,
                    de=text,
                    en=english,
                    author=WIKTIONARY_AUTHOR,
                    licence=WIKTIONARY_LICENCE,
                    native=False,
                    hl=span,
                    en_author=WIKTIONARY_AUTHOR if english else None,
                    en_licence=WIKTIONARY_LICENCE if english else None,
                )
                candidate.score = score(candidate, len(toks), word.lemma)
                found.setdefault(candidate.id, candidate)
    return sorted(found.values(), key=Candidate.order)


def final(
    tatoeba: list[Candidate],
    examples: list[Candidate],
    pinned: list[Candidate],
    banned: set[str],
) -> list[Candidate]:
    """Pinned sentences in their order, then the best of the rest, KEEP in all."""
    rest = sorted(
        (c for c in tatoeba + examples if c.id not in banned and c.id not in {p.id for p in pinned}),
        key=Candidate.order,
    )
    return (pinned + rest)[: max(KEEP, len(pinned))]
