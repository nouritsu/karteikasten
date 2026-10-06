from karteikasten_pipeline.stages.media import AudioCandidate, author, author_coverage, pick_audio, usable

# Artist values as the Commons API returns them (extmetadata, HTML).
JEUWRE = '<a href="//commons.wikimedia.org/wiki/User:Jeuwre" title="User:Jeuwre">Jeuwre</a>'
KAMPY = (
    '<a href="//commons.wikimedia.org/w/index.php?title=User:Kampy&amp;action=edit&amp;redlink=1" class="new"'
    ' title="User:Kampy (page does not exist)">Kampy</a>'
)
WALLROTH = (
    '<ul><li>Speaker: <a href="//lingualibre.org/wiki/Q124281" class="extiw" title="lingualibre:Q124281">'
    'Sebastian Wallroth</a></li>\n<li>Recorder: <a href="//commons.wikimedia.org/wiki/User:Sebastian_Wallroth"'
    ' title="User:Sebastian Wallroth">Sebastian Wallroth</a></li></ul>'
)
REDLINUX = (
    'No machine-readable author provided. <a href="//commons.wikimedia.org/wiki/User:Redlinux"'
    ' title="User:Redlinux">Redlinux</a> assumed (based on copyright claims).'
)
OWN_WORK = '<span class="int-own-work" lang="en">Own work</span>'


def info(artist: str | None, licence: str = "CC BY-SA 4.0") -> dict:
    return {"extmetadata": {"Artist": {"value": artist}, "LicenseShortName": {"value": licence}}}


def test_author_is_the_first_named_person():
    assert author(info(JEUWRE)) == "jeuwre"
    assert author(info(KAMPY)) == "kampy"
    assert author(info(WALLROTH)) == "sebastian wallroth"  # the speaker, listed first
    assert author(info(REDLINUX)) == "redlinux"
    assert author(info("T.Voekler")) == "t.voekler"
    assert author(info(OWN_WORK)) is None
    assert author(info("myself")) is None


def test_one_person_is_one_author_however_the_field_spells_them():
    lower = '<a href="//commons.wikimedia.org/wiki/User:Jeuwre" title="User:Jeuwre">jeuwre</a>'
    assert author(info(lower)) == author(info(JEUWRE))
    prefixed = '<a href="//commons.wikimedia.org/wiki/User:Tosca" title="User:Tosca">User:Tosca</a>'
    assert author(info(prefixed)) == author(info("Tosca"))


def test_files_need_author_and_licence_and_public_skips_nc_nd():
    assert not usable(None, "personal")
    assert not usable(info(None), "personal")
    assert not usable(info(JEUWRE, licence=""), "personal")
    assert usable(info(OWN_WORK), "personal")  # credited as Commons gives it, ranked last
    assert usable(info(JEUWRE, "CC BY-NC-SA 4.0"), "personal")
    assert not usable(info(JEUWRE, "CC BY-NC-SA 4.0"), "public")
    assert not usable(info(JEUWRE, "CC BY-ND 4.0"), "public")
    assert usable(info(JEUWRE, "CC BY-SA 4.0"), "public")


def candidate(file: str, region: str | None = None, germany: bool = False) -> AudioCandidate:
    return AudioCandidate(file=file, region=region, germany=germany)


LL = "LL-Q188 (deu)-Sebastian Wallroth-{}.wav"
CANDIDATES = {
    "Hand": [candidate("De-Hand.ogg"), candidate(LL.format("Hand"))],
    "Haus": [candidate("De-Haus.ogg")],
    "Mann": [candidate("De-Mann.ogg")],
    "gut": [candidate("De-gut.ogg", germany=True), candidate("De-gut2.ogg")],
    "fahren": [candidate("De-fahren.ogg"), candidate(LL.format("fahren"))],
    "Ding": [candidate("Ding.ogg"), candidate(LL.format("Ding"))],
    "Tag": [candidate("De-at-Tag.ogg", region="Austria"), candidate("Tag.ogg")],
    "Zeit": [candidate("Zeit.ogg")],  # Commons returned nothing for it
}
INFOS = {
    "De-Hand.ogg": info(JEUWRE),
    "De-Haus.ogg": info(JEUWRE),
    "De-Mann.ogg": info(JEUWRE),
    "De-gut2.ogg": info(JEUWRE),
    "De-at-Tag.ogg": info(JEUWRE),
    "De-gut.ogg": info(KAMPY),
    "De-fahren.ogg": info(KAMPY),
    LL.format("Hand"): info(WALLROTH),
    LL.format("fahren"): info(WALLROTH),
    LL.format("Ding"): info(WALLROTH),
    "Ding.ogg": info(OWN_WORK),
    "Tag.ogg": info("T.Voekler"),
}


def test_coverage_counts_words_with_a_standard_file():
    assert author_coverage(CANDIDATES, INFOS, "personal") == {
        "jeuwre": 4,  # the Austrian file does not count
        "sebastian wallroth": 3,
        "kampy": 2,
        "t.voekler": 1,
    }


def test_words_fall_through_to_authors_with_less_coverage():
    coverage = author_coverage(CANDIDATES, INFOS, "personal")
    picks = {word: pick_audio(cands, INFOS, coverage, "personal") for word, cands in CANDIDATES.items()}
    assert {word: pick.file if pick else None for word, pick in picks.items()} == {
        "Hand": "De-Hand.ogg",
        "Haus": "De-Haus.ogg",
        "Mann": "De-Mann.ogg",
        "gut": "De-gut2.ogg",  # coverage outranks the other file's Germany tag
        "fahren": LL.format("fahren"),  # no Jeuwre file: the next author by coverage, not by name
        "Ding": LL.format("Ding"),  # a named author before an anonymous file
        "Tag": "Tag.ogg",  # standard German before the top author's regional file
        "Zeit": None,  # no author or licence, so nothing to credit
    }
