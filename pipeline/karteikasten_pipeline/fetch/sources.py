"""Every upstream file the pipeline reads, pinned to a version wherever the upstream has one.

Commons audio and ARASAAC images are fetched per word once the deck's words are
known; everything here is a whole-file snapshot. Field notes: docs/sources/.
"""

from dataclasses import dataclass

GITHUB_RAW = "https://raw.githubusercontent.com"
FREQUENCYWORDS_COMMIT = "072bbed282316a23651aa7068c7173aa7898cf80"
UD_RELEASE = "r2.18"
OPENMOJI_RELEASE = "17.0.0"
CLDR_RELEASE = "release-48-2"
LEIPZIG = "https://downloads.wortschatz-leipzig.de/corpora"
TATOEBA = "https://downloads.tatoeba.org/exports/per_language"
DEREWO_PAGE = (
    "https://www.ids-mannheim.de/en/s/corpus-linguistics/projects/methods-of-analysis/"
    "corpus-based-lemma-and-word-form-lists/"
)


@dataclass(frozen=True)
class RawFile:
    path: str  # relative to data/raw
    url: str


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    licence: str
    files: tuple[RawFile, ...]
    # Set for files placed by hand: fetch records them in the lock but never downloads.
    manual: str | None = None


def _ud(treebank: str, names: tuple[str, ...]) -> tuple[RawFile, ...]:
    repo = f"{GITHUB_RAW}/UniversalDependencies/UD_German-{treebank}/{UD_RELEASE}"
    return tuple(RawFile(f"ud/{treebank.lower()}/{name}", f"{repo}/{name}") for name in names)


def _tatoeba(lang: str, names: tuple[str, ...]) -> tuple[RawFile, ...]:
    return tuple(RawFile(f"tatoeba/{name}", f"{TATOEBA}/{lang}/{name}") for name in names)


SOURCES: tuple[Source, ...] = (
    Source(
        id="frequencywords",
        name="FrequencyWords, OpenSubtitles 2018 (de)",
        licence="CC BY-SA 4.0",
        files=(
            RawFile(
                "frequencywords/de_full.txt",
                f"{GITHUB_RAW}/hermitdave/FrequencyWords/{FREQUENCYWORDS_COMMIT}/content/2018/de/de_full.txt",
            ),
        ),
    ),
    Source(
        id="leipzig",
        name="Leipzig Corpora Collection, German news 2025 and German web 2021 (1M sentences each)",
        licence="CC BY 4.0",
        files=tuple(
            RawFile(f"leipzig/{name}.tar.gz", f"{LEIPZIG}/{name}.tar.gz")
            for name in ("deu_news_2025_1M", "deu-de_web_2021_1M")
        ),
    ),
    Source(
        id="derewo",
        name="DeReWo lemma list 2012 (IDS Mannheim), private cross-check only",
        licence="IDS: non-commercial use, never passed on without its documentation",
        files=(
            RawFile(
                "derewo/derewo-v-ww-bll-320000g-2012-12-31-1.0.zip",
                "https://www.ids-mannheim.de/fileadmin/kl/derewo/derewo-v-ww-bll-320000g-2012-12-31-1.0.zip",
            ),
        ),
        manual=f"Download it from {DEREWO_PAGE} and put it in data/raw/derewo/.",
    ),
    Source(
        id="ud",
        name=f"Universal Dependencies German GSD and HDT ({UD_RELEASE})",
        licence="CC BY-SA 4.0",
        files=_ud("GSD", ("LICENSE.txt", "de_gsd-ud-train.conllu", "de_gsd-ud-dev.conllu", "de_gsd-ud-test.conllu"))
        + _ud(
            "HDT",
            (
                "LICENSE.txt",
                "de_hdt-ud-train-a-1.conllu",
                "de_hdt-ud-train-a-2.conllu",
                "de_hdt-ud-train-b-1.conllu",
                "de_hdt-ud-train-b-2.conllu",
                "de_hdt-ud-dev.conllu",
                "de_hdt-ud-test.conllu",
            ),
        ),
    ),
    # D23: Kaikki deprecated its per-language German file; stage 20 extracts the
    # German entries from the full dump instead.
    Source(
        id="kaikki-en",
        name="Kaikki, English Wiktionary (raw wiktextract dump, all languages)",
        licence="CC BY-SA 4.0 and GFDL",
        files=(
            RawFile(
                "kaikki-en/raw-wiktextract-data.jsonl.gz",
                "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
            ),
        ),
    ),
    Source(
        id="kaikki-de",
        name="Kaikki, German Wiktionary extract",
        licence="CC BY-SA 4.0 and GFDL",
        files=(
            RawFile(
                "kaikki-de/de-extract.jsonl.gz",
                "https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz",
            ),
        ),
    ),
    Source(
        id="arasaac",
        name="ARASAAC pictograms, German keywords",
        licence="CC BY-NC-SA 4.0",
        files=(RawFile("arasaac/pictograms-de.json", "https://api.arasaac.org/v1/pictograms/all/de"),),
    ),
    Source(
        id="openmoji",
        name=f"OpenMoji {OPENMOJI_RELEASE}",
        licence="CC BY-SA 4.0",
        files=(
            RawFile(
                "openmoji/openmoji.json",
                f"{GITHUB_RAW}/hfg-gmuend/openmoji/{OPENMOJI_RELEASE}/data/openmoji.json",
            ),
            RawFile(
                "openmoji/openmoji-svg-color.zip",
                f"https://github.com/hfg-gmuend/openmoji/releases/download/{OPENMOJI_RELEASE}/openmoji-svg-color.zip",
            ),
        ),
    ),
    Source(
        id="cldr",
        name=f"Unicode CLDR German emoji annotations ({CLDR_RELEASE})",
        licence="Unicode License v3",
        files=(
            RawFile(
                "cldr/annotations-de.xml",
                f"{GITHUB_RAW}/unicode-org/cldr/{CLDR_RELEASE}/common/annotations/de.xml",
            ),
            RawFile(
                "cldr/annotationsDerived-de.xml",
                f"{GITHUB_RAW}/unicode-org/cldr/{CLDR_RELEASE}/common/annotationsDerived/de.xml",
            ),
        ),
    ),
    Source(
        id="koeper",
        name="Köper & Schulte im Walde (2016) norms for 350,000 German lemmas",
        licence="CC BY-NC-SA 4.0",
        files=(
            RawFile(
                "koeper/affective_norms.txt.gz",
                "https://www.ims.uni-stuttgart.de/documents/ressourcen/experiment-daten/affective_norms.txt.gz",
            ),
        ),
    ),
    Source(
        id="tatoeba",
        name="Tatoeba German sentences with English translations",
        licence="CC BY 2.0 FR (some CC0)",
        files=_tatoeba(
            "deu",
            (
                "deu_sentences_detailed.tsv.bz2",
                "deu_sentences_CC0.tsv.bz2",
                "deu-eng_links.tsv.bz2",
                "deu_tags.tsv.bz2",
                "deu_user_languages.tsv.bz2",
            ),
        )
        + _tatoeba("eng", ("eng_sentences_detailed.tsv.bz2", "eng_sentences_CC0.tsv.bz2")),
    ),
)

BY_ID = {source.id: source for source in SOURCES}
