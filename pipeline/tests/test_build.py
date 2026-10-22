"""The real build on a tiny snapshot (fixtures/snapshot.tar.gz, see make_snapshot.py).

Checks the spec's tricky words (Testing), that every item carries its credit,
that overrides apply and fail when stale, and that two builds in separate
processes, with different hash seeds, write byte-identical decks.
"""

import json
import math
import os
import sqlite3
import struct
import subprocess
import sys
import tarfile
import wave
from pathlib import Path

import pytest

from karteikasten_pipeline import build
from karteikasten_pipeline.fetch import lock
from karteikasten_pipeline.fetch.http import sha256_of
from karteikasten_pipeline.paths import Paths
from karteikasten_pipeline.stages import bundle

PIPELINE = Path(__file__).resolve().parents[1]
SNAPSHOT = Path(__file__).parent / "fixtures" / "snapshot.tar.gz"
CONFIG = """\
n_max = 400
profile = "personal"

[frequency]
spoken_weight = 0.7
epsilon = 0.1

[http]
contact = "https://example.invalid"
"""
WORDS_TOML = """\
[exclude]
"äh#intj#1" = "filler"
"""


def _tone(pitch: int) -> bytes:
    """A second of 16 kHz mono: silence, half a second of the pitch, silence."""
    rate = 16000
    return b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * pitch * i / rate)) if rate // 4 <= i < rate * 3 // 4 else 0)
        for i in range(rate)
    )


# Five different files, so each build runs ffmpeg on more than one input.
TONES = [_tone(330 + 110 * k) for k in range(5)]


def checkout(root: Path, words_toml: str = WORDS_TOML, sentences_toml: str = "") -> Paths:
    """A checkout with the fixture snapshot in data/raw, a tone for each Commons file
    it names, and a lock that records every file."""
    (root / "config").mkdir(parents=True)
    (root / "config" / "pipeline.toml").write_text(CONFIG)
    (root / "overrides").mkdir()
    (root / "overrides" / "words.toml").write_text(words_toml)
    (root / "overrides" / "sentences.toml").write_text(sentences_toml)
    raw = root / "data" / "raw"
    with tarfile.open(SNAPSHOT) as tar:
        tar.extractall(raw, filter="data")
    pages = json.loads((raw / "commons" / "info" / "fixture.json").read_text())["query"]["pages"]
    for number, page in enumerate(p for p in pages if not p.get("missing")):
        path = raw / "commons" / "audio" / page["title"].removeprefix("File:")
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as out:  # WAV bytes under the .ogg name: ffmpeg reads the content
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(16000)
            out.writeframes(TONES[number % len(TONES)])
    entries = {}
    for path in sorted(p for p in raw.rglob("*") if p.is_file()):
        relative = path.relative_to(raw).as_posix()
        entries[relative] = lock.Entry(
            source=relative.split("/")[0], url=f"https://example.invalid/{relative}",
            retrieved_at="2026-10-06T12:00:00Z", bytes=path.stat().st_size, sha256=sha256_of(path),
        )
    lock.save(root / "sources.lock.json", entries)
    return Paths(root)


def quiet(_: str) -> None:
    pass


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    paths = checkout(tmp_path_factory.mktemp("checkout"))
    dest = build.run(paths, offline=True, log=quiet)
    words = {w["id"]: w for w in json.loads((dest / "words.json").read_text())}
    return paths, dest, words


# -- tricky words ---------------------------------------------------------------------------


def test_sein_verb_and_determiner_are_two_ids_with_split_counts(deck):
    _, _, words = deck
    assert words["sein#verb#1"]["token_share"] > words["sein#det#2"]["token_share"] > 0


def test_die_splits_between_article_and_pronoun(deck):
    _, _, words = deck
    assert words["der#article#1"]["token_share"] > words["der#pron#1"]["token_share"] > 0


def test_bank_etymologies_have_their_own_plurals(deck):
    _, _, words = deck
    assert words["Bank#noun#1"]["key_forms"]["plural"] == "Bänke"
    assert words["Bank#noun#2"]["key_forms"]["plural"] == "Banken"


@pytest.mark.parametrize("ids", [("Essen#noun#1", "essen#verb#1"), ("Morgen#noun#1", "morgen#adv#1"),
                                 ("Sie#pron#1", "sie#pron#1")])
def test_case_variants_are_separate_words(deck, ids):
    _, _, words = deck
    assert all(id_ in words for id_ in ids)


@pytest.mark.parametrize("verb", ["anfangen", "aufhören", "ankommen", "anrufen"])
def test_separable_verbs_are_flagged_and_scaled(deck, verb):
    _, _, words = deck
    word = words[f"{verb}#verb#1"]
    assert "separable" in word["flags"]
    assert word["key_forms"]["particle"] == verb[:2] if verb.startswith("an") else verb[:3]
    assert "separable-scaled" in word["frequency_flags"]


@pytest.mark.parametrize(("id_", "genitive"), [("Junge#noun#1", "Jungen"), ("Herr#noun#1", "Herrn")])
def test_weak_nouns(deck, id_, genitive):
    _, _, words = deck
    assert "weak_noun" in words[id_]["flags"]
    assert words[id_]["key_forms"]["genitive"] == genitive


@pytest.mark.parametrize("id_", ["Leute#noun#1", "Eltern#noun#1"])
def test_plural_only_nouns(deck, id_):
    _, _, words = deck
    assert "plural_only" in words[id_]["flags"]
    assert words[id_]["article"] == "die"


def test_auxiliaries_modals_and_stem_changes(deck):
    _, _, words = deck
    k = {v: words[f"{v}#verb#1"]["key_forms"] for v in ("haben", "werden", "können", "wissen", "fahren")}
    assert (k["haben"]["er"], k["haben"]["praeteritum"], k["haben"]["partizip2"]) == ("hat", "hatte", "gehabt")
    assert (k["werden"]["er"], k["werden"]["praeteritum"], k["werden"]["partizip2"]) == ("wird", "wurde", "geworden")
    assert "sein" in k["werden"]["auxiliary"]
    assert (k["können"]["er"], k["können"]["praeteritum"]) == ("kann", "konnte")
    assert (k["wissen"]["er"], k["wissen"]["praeteritum"]) == ("weiß", "wusste")
    assert (k["fahren"]["er"], k["fahren"]["du"], k["fahren"]["praeteritum"]) == ("fährt", "fährst", "fuhr")
    assert set(k["fahren"]["auxiliary"]) == {"haben", "sein"}
    for modal in ("können", "wissen"):
        assert "preterite_present" in words[f"{modal}#verb#1"]["flags"]


def test_sich_freuen_is_reflexive(deck):
    _, _, words = deck
    assert "reflexive" in words["freuen#verb#1"]["flags"]


def test_irregular_comparison_and_stem(deck):
    _, _, words = deck
    assert words["gut#adj#1"]["key_forms"]["comparative"] == "besser"
    assert words["viel#det#1"]["key_forms"]["comparative"] == "mehr"
    assert words["gern#adv#1"]["key_forms"]["comparative"] == "lieber"
    assert words["hoch#adj#1"]["key_forms"]["comparative"] == "höher"
    assert words["hoch#adj#1"]["key_forms"]["attributive"] == "hohe"


@pytest.mark.parametrize(("id_", "case"), [("mit#prep#1", "dat"), ("für#prep#1", "acc"), ("in#prep#1", "two-way"),
                                           ("wegen#prep#1", "gen")])
def test_preposition_cases_from_wiktionary(deck, id_, case):
    _, _, words = deck
    assert words[id_]["key_forms"]["case"] == case


def test_contractions_belong_to_their_preposition(deck):
    _, _, words = deck
    assert {"im", "ins"} <= set(words["in#prep#1"]["key_forms"]["contractions"])


@pytest.mark.parametrize(("id_", "kind"), [("weil#conj#1", "subordinating"), ("und#conj#1", "coordinating")])
def test_conjunction_types(deck, id_, kind):
    _, _, words = deck
    assert words[id_]["key_forms"]["conjunction"] == kind


@pytest.mark.parametrize("word", ["doch", "mal"])
def test_particles_are_usage_only(deck, word):
    _, _, words = deck
    assert any("context_dependent" in w["flags"] for id_, w in words.items() if id_.startswith(f"{word}#"))


@pytest.mark.parametrize("word", ["ja", "danke", "okay"])
def test_interjections_are_kept(deck, word):
    _, _, words = deck
    assert any(id_.startswith(f"{word}#") for id_ in words)


def test_filler_is_excluded(deck):
    _, _, words = deck
    assert not any(id_.startswith("äh#") for id_ in words)


# -- other stage 40 content -------------------------------------------------------------------


def test_numeral_ordinal(deck):
    _, _, words = deck
    assert words["zwei#num#1"]["key_forms"]["ordinal"] == "zweite"


def test_case_tables(deck):
    _, _, words = deck
    article = words["der#article#1"]["tables"]["cases"]
    assert article["columns"] == ["m", "f", "n", "pl"]
    assert article["rows"][0] == {"case": "nominative", "cells": ["der", "die", "das", "die"]}
    ich = words["ich#pron#1"]["tables"]["cases"]
    assert ich["columns"] == ["sg", "pl"]
    assert [row["cells"] for row in ich["rows"]] == [["ich", "wir"], ["meiner", "unser"], ["mir", "uns"],
                                                       ["mich", "uns"]]


def test_cognates_only_when_glossed(deck):
    _, _, words = deck
    assert words["Haus#noun#1"]["cognate_en"] == "house"
    assert words["schon#adv#1"]["cognate_en"] is None  # etymology: English sheen; it means "already"


# -- credits and bundle -----------------------------------------------------------------------


def test_every_audio_file_and_sentence_is_credited(deck):
    _, _, words = deck
    assert any(w["audio"] for w in words.values())
    for w in words.values():
        for item in ([w["audio"]] if w["audio"] else []) + w["sentences"]:
            assert item["source"] and item["author"] and item["license"], item
        for s in w["sentences"]:
            assert (s["en"] is None) == (s["en_author"] is None)


def test_sentences_know_their_deck_words(deck):
    _, _, words = deck
    sentence = next(s for w in words.values() for s in w["sentences"])
    assert sentence["deck_token_ids"] and sentence["out_of_deck"] >= 0
    assert all(id_ in words for id_ in sentence["deck_token_ids"])


def test_bundle_files_and_sqlite_agree(deck):
    paths, dest, words = deck
    assert {p.name for p in dest.iterdir()} == {"manifest.json", "deck.sqlite", "words.json", "attribution.json",
                                                "coverage.md", "media"}
    manifest = json.loads((dest / "manifest.json").read_text())
    assert manifest["deck_version"] == dest.name and dest.name.startswith("2026.10.06-")
    assert json.loads((paths.dist / "deck" / "latest.json").read_text()) == {"version": dest.name}
    con = sqlite3.connect(dest / "deck.sqlite")
    assert con.execute("SELECT count(*) FROM word").fetchone()[0] == len(words)
    assert con.execute("SELECT count(*) FROM sentence").fetchone()[0] == sum(len(w["sentences"]) for w in words.values())
    audio = con.execute("SELECT count(*) FROM media WHERE kind = 'audio'").fetchone()[0]
    assert audio == manifest["counts"]["audio"] == len(list((dest / "media" / "audio").iterdir()))
    assert (paths.work / "curation.sqlite").exists()


# -- overrides --------------------------------------------------------------------------------


def test_overrides_apply(deck, tmp_path):
    _, _, before = deck
    hand = before["Hand#noun#1"]["sentences"]
    assert len(hand) >= 2
    words_toml = WORDS_TOML + """
[merge]
"okay#adj#1" = "okay#intj#1"

[gloss_en]
"Hand#noun#1" = ["hand (by hand)"]

[no_cognate]
"Haus#noun#1" = "test"
"""
    sentences_toml = f"""
[pin]
"Hand#noun#1" = ["{hand[-1]['id']}"]

[ban]
"Hand#noun#1" = ["{hand[0]['id']}"]
"""
    paths = checkout(tmp_path, words_toml, sentences_toml)
    words = {w["id"]: w for w in json.loads((build.run(paths, offline=True, log=quiet) / "words.json").read_text())}
    assert "okay#adj#1" not in words and "merged" in words["okay#intj#1"]["frequency_flags"]
    assert words["Hand#noun#1"]["gloss_en"] == [{"text": "hand (by hand)", "tags": []}]
    assert words["Hand#noun#1"]["provenance"]["gloss_en"].startswith("manual")
    assert words["Haus#noun#1"]["cognate_en"] is None
    ids = [s["id"] for s in words["Hand#noun#1"]["sentences"]]
    assert ids[0] == hand[-1]["id"] and hand[0]["id"] not in ids


@pytest.mark.parametrize(
    ("words_toml", "sentences_toml", "message"),
    [
        (WORDS_TOML + '\n[gloss_en]\n"Nichtwort#noun#1" = ["x"]\n', "", "Nichtwort#noun#1"),
        (WORDS_TOML + '\n[no_cognate]\n"mit#prep#1" = "x"\n', "", "no cognate hint"),
        (WORDS_TOML, '[ban]\n"Hand#noun#1" = ["tatoeba:1"]\n', "not a sentence for this word"),
    ],
)
def test_stale_overrides_fail_the_build(tmp_path, words_toml, sentences_toml, message):
    paths = checkout(tmp_path, words_toml, sentences_toml)
    with pytest.raises(build.BuildError, match=message):
        build.run(paths, offline=True, log=quiet)


# -- determinism ------------------------------------------------------------------------------


def test_two_builds_are_byte_identical(tmp_path):
    decks = []
    for seed in (1, 2):
        root = tmp_path / f"run{seed}"
        checkout(root)
        # Prepend: under Nix the dependencies are found through PYTHONPATH too.
        path = os.pathsep.join(p for p in (str(PIPELINE), os.environ.get("PYTHONPATH", "")) if p)
        env = {**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONPATH": path}
        result = subprocess.run(
            [sys.executable, "-m", "karteikasten_pipeline", "--root", str(root), "build", "--offline"],
            env=env, cwd=PIPELINE, capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        decks.append(Path(result.stdout.strip()))
    assert decks[0].name == decks[1].name
    assert bundle.tree_digest(decks[0]) == bundle.tree_digest(decks[1])
