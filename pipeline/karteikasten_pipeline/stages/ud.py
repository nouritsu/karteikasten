"""Universal Dependencies statistics for stage 30.

- `analyses`: how often each lower-cased surface token is which (lemma, UPOS,
  STTS tag); splits ambiguous forms such as "die" (article or pronoun). The STTS
  tag tells negation "nicht" (PTKNEG), infinitive "zu" (PTKZU) and postposed
  "nach" (APPO) apart, which UPOS alone does not.
- particle verbs: how often each occurs split ("rief ... an": the particle hangs
  off the finite verb as compound:prt, which keeps the base lemma "rufen") and
  unsplit ("anrufen", "angerufen", "anzurufen": lemma "anrufen"). Frequency lists
  only see unsplit forms, so stage 30 scales those by the split/unsplit ratio,
  discounts base verbs by how often they are really a split particle verb, and
  does not count separated particles (STTS PTKVZ) as prepositions.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from karteikasten_pipeline.readers import conllu

VERBAL = frozenset({"VERB", "AUX"})
SEPARATED_PARTICLE = "PTKVZ"


@dataclass
class UdStats:
    analyses: Counter[tuple[str, str, str, str]] = field(default_factory=Counter)
    split: Counter[str] = field(default_factory=Counter)  # particle verb -> split uses
    unsplit: Counter[str] = field(default_factory=Counter)  # verbal lemma -> tokens with that lemma
    split_heads: Counter[str] = field(default_factory=Counter)  # base verb -> tokens heading a particle
    by_token: dict[str, list[tuple[str, str, str, int]]] = field(default_factory=dict, repr=False)

    def add(self, sentence: list[conllu.Word]) -> None:
        by_id = {word.id: word for word in sentence}
        for word in sentence:
            if word.token_start:
                self.analyses[(word.token.lower(), word.lemma, word.upos, word.xpos)] += 1
            if word.upos in VERBAL:
                self.unsplit[word.lemma] += 1
            if word.deprel == "compound:prt":
                head = by_id.get(word.head)
                if head is not None and head.upos in VERBAL:
                    self.split[word.lemma.lower() + head.lemma] += 1
                    self.split_heads[head.lemma] += 1

    def index(self) -> None:
        """Group the analyses by token; call once all sentences are added."""
        self.by_token = {}
        for (token, lemma, upos, xpos), n in sorted(self.analyses.items()):
            self.by_token.setdefault(token, []).append((lemma, upos, xpos, n))

    def for_token(self, token: str) -> list[tuple[str, str, str, int]]:
        return self.by_token.get(token, [])

    @property
    def particle_verbs(self) -> set[str]:
        """Verbs seen split at least once."""
        return set(self.split)

    def split_ratio(self, lemma: str | None = None, prior_weight: float = 10.0) -> float:
        """Split per unsplit occurrence: over all particle verbs, or for one verb
        shrunk toward the overall ratio (`prior_weight` pseudo-occurrences)."""
        verbs = self.particle_verbs
        overall = sum(self.split[v] for v in verbs) / max(1, sum(self.unsplit[v] for v in verbs))
        if lemma is None:
            return overall
        return (self.split[lemma] + prior_weight * overall) / (self.unsplit[lemma] + prior_weight)

    def head_share(self, base: str, prior_weight: float = 10.0) -> float:
        """Share of a base verb's tokens that are really a split particle verb
        ("fängt" in "fängt ... an"), shrunk toward the overall share."""
        overall = sum(self.split_heads.values()) / max(1, sum(self.unsplit.values()))
        return (self.split_heads[base] + prior_weight * overall) / (self.unsplit[base] + prior_weight)

    def separated_share(self, token: str) -> float:
        """Share of a token's uses as a separated verb particle (STTS PTKVZ)."""
        rows = self.for_token(token)
        total = sum(n for *_, n in rows)
        return sum(n for _, _, xpos, n in rows if xpos == SEPARATED_PARTICLE) / total if total else 0.0


def collect(paths: Iterable[Path]) -> UdStats:
    stats = UdStats()
    for path in paths:
        for sentence in conllu.read(path):
            stats.add(sentence)
    stats.index()
    return stats
