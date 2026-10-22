import pytest

from karteikasten_pipeline import overrides
from karteikasten_pipeline.overrides import OverrideError


def write(directory, name, text):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding="utf-8")


def test_missing_files_mean_no_overrides(tmp_path):
    loaded = overrides.load(tmp_path)
    assert loaded.ids() == set()


def test_every_table_is_read(tmp_path):
    write(tmp_path, "words.toml", """
[exclude]
"äh#intj#1" = "filler"
[merge]
"sie#pron#2" = "sie#pron#1"
[gloss_en]
"Dr.#noun#1" = ["doctor (title)"]
[no_cognate]
"Kraft#noun#1" = "craft misleads"
[audio]
"Hand#noun#1" = "De-Hand2.ogg"
""")
    write(tmp_path, "closed_classes.toml", """
[preposition]
"in#prep#1" = { cases = ["acc", "dat"], contractions = ["im", "ins"] }
"wegen#prep#1" = { cases = ["gen", "dat"] }
[conjunction]
"weil#conj#1" = "subordinating"
""")
    write(tmp_path, "sentences.toml", """
[pin]
"Hand#noun#1" = ["tatoeba:2"]
[ban]
"Hand#noun#1" = ["tatoeba:1"]
""")
    write(tmp_path / "audio", "Dr._noun_1.flac", "")
    loaded = overrides.load(tmp_path)
    assert loaded.words.merge == {"sie#pron#2": "sie#pron#1"}
    assert loaded.words.audio == {"Hand#noun#1": "De-Hand2.ogg"}
    assert loaded.closed.prepositions["in#prep#1"] == ["acc", "dat"]
    assert loaded.closed.contractions == {"in#prep#1": ["im", "ins"]}
    assert loaded.closed.conjunctions == {"weil#conj#1": "subordinating"}
    assert loaded.sentences.pin == {"Hand#noun#1": ["tatoeba:2"]}
    assert loaded.recordings == {"Dr.#noun#1": tmp_path / "audio" / "Dr._noun_1.flac"}
    known = loaded.ids() - {"Kraft#noun#1"}
    assert overrides.unmatched(loaded, known) == ["Kraft#noun#1"]


def test_recording_names_keep_underscores_in_the_lemma():
    from pathlib import Path

    assert overrides.recording_id(Path("wie_viel_det_1.flac")) == "wie_viel#det#1"


@pytest.mark.parametrize(
    ("name", "text", "message"),
    [
        ("closed_classes.toml", '[preposition]\n"mit#prep#1" = { cases = ["dative"] }\n', "cases"),
        ("closed_classes.toml", '[preposition]\n"mit#prep#1" = { cases = [] }\n', "cases"),
        ("closed_classes.toml", '[conjunction]\n"weil#conj#1" = "sub"\n', "not one of"),
        ("words.toml", '[merge]\n"a#x#1" = "b#x#1"\n"b#x#1" = "c#x#1"\n', "itself joins"),
        ("words.toml", '[gloss_en]\n"a#x#1" = "not a list"\n', "list of strings"),
        ("words.toml", '[audio]\n"a#x#1" = ["De-a.ogg"]\n', "Commons file name"),
        ("words.toml", "[exclude\n", "words.toml"),
    ],
)
def test_malformed_overrides_are_errors(tmp_path, name, text, message):
    write(tmp_path, name, text)
    with pytest.raises(OverrideError, match=message):
        overrides.load(tmp_path)


def test_a_recording_needs_a_word_id_name(tmp_path):
    write(tmp_path / "audio", "Hand.flac", "")
    with pytest.raises(OverrideError, match="word id"):
        overrides.load(tmp_path)
