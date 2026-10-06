"""Stage 30: frequency and lemmas.

1. Word-form counts: spoken from FrequencyWords (OpenSubtitles 2018, case-folded),
   written from Leipzig news 2025 + German web 2021 (case kept). Both are keyed by
   lower case and shared out over the cased forms the lexicon knows, by Leipzig's
   ratio of each spelling away from sentence- or quote-initial positions
   (Essen/essen, Sie/sie).
2. Lemmas: each cased form is split over its candidate lemmas by UD, add-one
   smoothed. A UD analysis counts for the candidates whose POS matches its UPOS
   (or, more weakly, its STTS tag: PTKNEG "nicht" is an adverb in Wiktionary) and,
   among those, the ones with UD's lemma. Forms UD never saw split evenly and are
   flagged. Homographs UD cannot tell apart (Bank: bench or bank) split by the
   mass of their unambiguous forms (Bänke vs Banken).
3. Separable verbs. Lists only see unsplit forms (anfangen, angefangen, anfängt),
   so particle verbs are scaled by 1 + UD's split/unsplit ratio. The split uses
   would otherwise also count twice: as the base verb ("fängt ... an" -> fangen)
   and as a preposition ("an"). So each base verb is discounted by its share of
   UD tokens that head a separated particle, and each particle token by its share
   of STTS PTKVZ uses (D25).
4. Blend: weighted geometric mean of per-million frequencies, plus epsilon.
5. Filter proper nouns, non-words, words without a German Wiktionary entry,
   digits and excluded ids, then rank. token_share is a lemma's share of all
   blended mass, including what was filtered or matched no lemma.
"""

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from karteikasten_pipeline.stages.lexicon import Lemma, Lexicon
from karteikasten_pipeline.stages.ud import SEPARATED_PARTICLE, UdStats

UPOS_MATCH = {
    "noun": {"NOUN"},
    "name": {"PROPN"},
    "verb": {"VERB", "AUX"},
    "adj": {"ADJ"},
    "adv": {"ADV"},
    "particle": {"PART"},
    "intj": {"INTJ"},
    "article": {"DET"},
    "det": {"DET"},
    "pron": {"PRON"},
    "prep": {"ADP"},
    "conj": {"CCONJ", "SCONJ"},
    "num": {"NUM"},
}
# STTS tags that match a Wiktionary POS more weakly than its UPOS would.
XPOS_MATCH = {
    "adv": {"PTKNEG"},
    "particle": {"PTKZU", "PTKA", "PTKANT", "PTKNEG"},
    "intj": {"PTKANT"},
}
NOT_WORDS = frozenset({"suffix", "prefix", "interfix", "circumfix", "character", "symbol", "punct", "infix"})
MILLION = 1_000_000.0
FLAG_SHARE = 0.1


def match_strength(pos: str, upos: str, xpos: str) -> int:
    """2: the UD analysis is this Wiktionary POS; 1: plausibly so; 0: not."""
    if pos == "postp":
        return 2 if xpos == "APPO" else 0
    if pos == "prep" and xpos == "APPO":
        return 0
    if upos in UPOS_MATCH.get(pos, ()):
        return 2
    if xpos in XPOS_MATCH.get(pos, ()):
        return 1
    return 0


@dataclass
class Ranked:
    rank: int
    id: str
    word: str
    pos: str
    spoken_pm: float
    written_pm: float
    blended_pm: float
    token_share: float
    coverage_cum: float
    flags: list[str]


@dataclass
class Result:
    ranked: list[Ranked]
    dropped: dict[str, str]  # lemma id -> why it is not ranked
    unmapped_share: float  # share of blended mass in forms that matched no lemma
    notes: dict[str, float | int] = field(default_factory=dict)


def case_shares(
    lower_keys: Iterable[str], lexicon: Lexicon, non_initial: Mapping[str, int]
) -> tuple[dict[str, list[tuple[str, float]]], set[str]]:
    """For each lower-case key, the lexicon's spellings of it with their shares,
    and the keys that had to be split evenly for lack of evidence."""
    spellings: dict[str, list[str]] = defaultdict(list)
    for form in lexicon.candidates:
        spellings[form.lower()].append(form)
    shares: dict[str, list[tuple[str, float]]] = {}
    even: set[str] = set()
    for key in lower_keys:
        forms = sorted(spellings.get(key, []))
        if not forms:
            continue
        weights = [non_initial.get(form, 0) for form in forms]
        total = sum(weights)
        if total > 0:
            shares[key] = [(form, w / total) for form, w in zip(forms, weights, strict=True) if w > 0]
        else:
            shares[key] = [(form, 1 / len(forms)) for form in forms]
            if len(forms) > 1:
                even.add(key)
    return shares, even


def ud_weights(form: str, lemmas: list[Lemma], ud: UdStats) -> tuple[dict[str, float], bool]:
    """Add-one smoothed UD evidence per candidate lemma, and whether UD saw the form at all."""
    weights = {lemma.id: 1.0 for lemma in lemmas}
    seen = False
    for ud_lemma, upos, xpos, n in ud.for_token(form.lower()):
        if xpos == SEPARATED_PARTICLE:
            continue
        strengths = {lemma.id: match_strength(lemma.pos, upos, xpos) for lemma in lemmas}
        best = max(strengths.values())
        if best == 0:
            continue
        targets = [lemma for lemma in lemmas if strengths[lemma.id] == best]
        targets = [lemma for lemma in targets if lemma.current] or targets
        # UD's lemma picks among them: exactly ("er", not archaic "Er"), else ignoring case.
        same_lemma = [lemma for lemma in targets if lemma.word == ud_lemma] or [
            lemma for lemma in targets if lemma.word.lower() == ud_lemma.lower()
        ]
        for lemma in same_lemma or targets:
            weights[lemma.id] += n / len(same_lemma or targets)
        seen = True
    return weights, seen


def lemma_shares(
    form: str, lexicon: Lexicon, ud: UdStats, homograph_mass: Mapping[str, float]
) -> tuple[list[tuple[str, float]], list[str]]:
    """Split one cased form over its candidate lemmas."""
    lemmas = [lexicon.lemmas[id_] for id_ in sorted(lexicon.candidates[form])]
    if len(lemmas) == 1:
        return [(lemmas[0].id, 1.0)], []
    weights, seen = ud_weights(form, lemmas, ud)
    flags = [] if seen else ["unseen-in-ud"]
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for lemma in lemmas:
        groups[(lemma.word, lemma.pos)].append(lemma.id)
    for members in groups.values():
        if len(members) > 1:
            total = sum(weights[id_] for id_ in members)
            mass = {id_: homograph_mass.get(id_, 0.0) + 1e-9 for id_ in members}
            for id_ in members:
                weights[id_] = total * mass[id_] / sum(mass.values())
            flags.append("homograph-split")
    total = sum(weights.values())
    return [(lemma.id, weights[lemma.id] / total) for lemma in lemmas], flags


def rank(
    spoken: Mapping[str, int],
    written: Mapping[str, tuple[int, int]],
    lexicon: Lexicon,
    ud: UdStats,
    *,
    spoken_weight: float,
    epsilon: float,
    exclude: Mapping[str, str],
) -> Result:
    # -- 1. per-million counts per cased form -------------------------------------------
    spoken_lower: dict[str, int] = defaultdict(int)
    for form, count in spoken.items():
        spoken_lower[form.lower()] += count
    spoken_total = sum(spoken_lower.values())
    written_lower: dict[str, int] = defaultdict(int)
    non_initial: dict[str, int] = {}
    for form, (total, initial) in written.items():
        if any(ch.isalnum() for ch in form):
            written_lower[form.lower()] += total
            non_initial[form] = total - initial
    written_total = sum(written_lower.values())

    keys = set(spoken_lower) | set(written_lower)
    shares, even_case = case_shares(keys, lexicon, non_initial)
    form_spoken: dict[str, float] = defaultdict(float)
    form_written: dict[str, float] = defaultdict(float)
    unmapped: dict[str, tuple[float, float]] = {}
    for key in sorted(keys):
        s = spoken_lower.get(key, 0) / spoken_total * MILLION
        w = written_lower.get(key, 0) / written_total * MILLION
        if key not in shares:
            unmapped[key] = (s, w)
            continue
        kept = 1.0 - ud.separated_share(key)
        for form, share in shares[key]:
            form_spoken[form] += s * share * kept
            form_written[form] += w * share * kept

    # -- 2. lemmas ----------------------------------------------------------------------
    etymologies = Counter((lemma.word, lemma.pos) for lemma in lexicon.lemmas.values())
    homograph_mass: dict[str, float] = defaultdict(float)
    for form in form_spoken.keys() | form_written.keys():
        by_word_pos: dict[tuple[str, str], list[str]] = defaultdict(list)
        for id_ in lexicon.candidates[form]:
            by_word_pos[(lexicon.lemmas[id_].word, lexicon.lemmas[id_].pos)].append(id_)
        for key, members in by_word_pos.items():
            if len(members) == 1 and etymologies[key] > 1:
                homograph_mass[members[0]] += form_spoken.get(form, 0.0) + form_written.get(form, 0.0)

    lemma_spoken: dict[str, float] = defaultdict(float)
    lemma_written: dict[str, float] = defaultdict(float)
    # Mass that reached a lemma through each kind of guess; a flag is only raised
    # when a guess carries a real part of the lemma (FLAG_SHARE), not a stray form.
    flag_mass: dict[str, Counter[str]] = defaultdict(Counter)
    for form in sorted(form_spoken.keys() | form_written.keys()):
        split, flags = lemma_shares(form, lexicon, ud, homograph_mass)
        if form.lower() in even_case:
            flags = [*flags, "even-case-split"]
        for id_, share in split:
            spoken_part = form_spoken.get(form, 0.0) * share
            written_part = form_written.get(form, 0.0) * share
            lemma_spoken[id_] += spoken_part
            lemma_written[id_] += written_part
            for flag in flags:
                flag_mass[id_][flag] += spoken_part + written_part
    lemma_flags: dict[str, set[str]] = defaultdict(set)
    for id_, masses in flag_mass.items():
        total = lemma_spoken[id_] + lemma_written[id_]
        lemma_flags[id_] = {flag for flag, m in masses.items() if total and m / total > FLAG_SHARE}

    # -- 3. separable verbs and their base verbs ------------------------------------------
    ratio = ud.split_ratio()
    for id_ in sorted(lemma_spoken.keys() | lemma_written.keys()):
        lemma = lexicon.lemmas[id_]
        if id_ in lexicon.separable:
            factor = 1 + ratio
            lemma_flags[id_].add("separable-scaled")
        elif lemma.pos == "verb":
            factor = 1 - ud.head_share(lemma.word)
        else:
            continue
        lemma_spoken[id_] *= factor
        lemma_written[id_] *= factor

    # -- 4. blend -----------------------------------------------------------------------
    def blend(s: float, w: float) -> float:
        return math.exp(spoken_weight * math.log(s + epsilon) + (1 - spoken_weight) * math.log(w + epsilon)) - epsilon

    blended = {id_: blend(lemma_spoken[id_], lemma_written[id_]) for id_ in lemma_spoken.keys() | lemma_written.keys()}
    unmapped_mass = sum(blend(s, w) for s, w in unmapped.values())
    mass = sum(blended.values()) + unmapped_mass

    # -- 5. filter and rank ---------------------------------------------------------------
    dropped: dict[str, str] = {}
    kept_ids: list[str] = []
    for id_ in blended:
        lemma = lexicon.lemmas[id_]
        if id_ in exclude:
            dropped[id_] = f"excluded: {exclude[id_]}"
        elif lemma.pos == "name":
            dropped[id_] = "proper noun"
        elif lemma.pos in NOT_WORDS:
            dropped[id_] = f"not a word ({lemma.pos})"
        elif any(ch.isdigit() for ch in lemma.word):
            dropped[id_] = "digits"
        elif not lexicon.in_german_wiktionary(lemma.word):
            dropped[id_] = "no German Wiktionary entry"
        else:
            kept_ids.append(id_)
    kept_ids.sort(key=lambda id_: (-blended[id_], id_))

    ranked: list[Ranked] = []
    coverage = 0.0
    for position, id_ in enumerate(kept_ids, start=1):
        share = blended[id_] / mass
        coverage += share
        lemma = lexicon.lemmas[id_]
        ranked.append(
            Ranked(
                rank=position,
                id=id_,
                word=lemma.word,
                pos=lemma.pos,
                spoken_pm=lemma_spoken[id_],
                written_pm=lemma_written[id_],
                blended_pm=blended[id_],
                token_share=share,
                coverage_cum=coverage,
                flags=sorted(lemma_flags[id_]),
            )
        )
    return Result(
        ranked=ranked,
        dropped=dropped,
        unmapped_share=unmapped_mass / mass,
        notes={
            "spoken_tokens": spoken_total,
            "written_tokens": written_total,
            "separable_ratio": ratio,
            "even_case_keys": len(even_case),
        },
    )
