import hashlib

import httpx

from karteikasten_pipeline import fetch
from karteikasten_pipeline.fetch import commons, lock
from karteikasten_pipeline.fetch.http import Client
from karteikasten_pipeline.fetch.sources import SOURCES, RawFile, Source

WORDS = Source(
    id="words",
    name="Test words",
    licence="CC0",
    files=(RawFile("words/list.txt", "https://files.example.org/list.txt"),),
)
HANDMADE = Source(
    id="handmade",
    name="Placed by hand",
    licence="private",
    files=(RawFile("handmade/list.zip", "https://files.example.org/list.zip"),),
    manual="Put it there yourself.",
)


def serving(body: bytes, requests: list):
    def handler(request):
        requests.append(request)
        return httpx.Response(200, content=body)

    return Client("https://example.org", transport=httpx.MockTransport(handler), min_interval=0)


def test_downloads_and_records_each_file(tmp_path):
    requests = []
    with serving(b"der\t100\n", requests) as client:
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], log=lambda _: None)

    entry = lock.load(tmp_path / "lock.json")["words/list.txt"]
    assert (tmp_path / "raw/words/list.txt").read_bytes() == b"der\t100\n"
    assert entry.source == "words"
    assert entry.url == "https://files.example.org/list.txt"
    assert entry.bytes == 8
    assert entry.sha256 == hashlib.sha256(b"der\t100\n").hexdigest()


def test_existing_snapshots_are_kept_unless_refreshed(tmp_path):
    requests = []
    with serving(b"a", requests) as client:
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], log=lambda _: None)
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], log=lambda _: None)
        assert len(requests) == 1
        fetch.run(
            tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], refresh=True, log=lambda _: None
        )
        assert len(requests) == 2


def test_a_refresh_with_identical_bytes_keeps_the_lock_entry(tmp_path):
    with serving(b"same", []) as client:
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], log=lambda _: None)
        before = (tmp_path / "lock.json").read_text()
        fetch.run(
            tmp_path / "raw", tmp_path / "lock.json", client, sources=[WORDS], refresh=True, log=lambda _: None
        )
    assert (tmp_path / "lock.json").read_text() == before


def test_manual_files_are_recorded_but_never_downloaded(tmp_path):
    requests, messages = [], []
    with serving(b"", requests) as client:
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[HANDMADE], log=messages.append)
        assert "Put it there yourself." in messages[0]
        assert lock.load(tmp_path / "lock.json") == {}

        (tmp_path / "raw/handmade").mkdir(parents=True)
        (tmp_path / "raw/handmade/list.zip").write_bytes(b"zip")
        fetch.run(tmp_path / "raw", tmp_path / "lock.json", client, sources=[HANDMADE], log=messages.append)

    assert requests == []
    entry = lock.load(tmp_path / "lock.json")["handmade/list.zip"]
    assert entry.sha256 == hashlib.sha256(b"zip").hexdigest()
    assert entry.url == "https://files.example.org/list.zip"


def test_lock_file_is_sorted_and_stable(tmp_path):
    entries = {
        "b/file": lock.Entry("b", "https://b", "2026-10-06T00:00:00Z", 2, "bb"),
        "a/file": lock.Entry("a", "https://a", "2026-10-06T00:00:00Z", 1, "aa"),
    }
    lock.save(tmp_path / "lock.json", entries)
    text = (tmp_path / "lock.json").read_text()
    assert text.index('"a/file"') < text.index('"b/file"')
    assert text.endswith("}\n")
    assert lock.load(tmp_path / "lock.json") == entries


def test_registry_paths_are_unique_and_relative():
    paths = [file.path for source in SOURCES for file in source.files]
    assert len(paths) == len(set(paths))
    assert all(not path.startswith("/") and ".." not in path for path in paths)
    assert all(file.url.startswith("https://") for source in SOURCES for file in source.files)


def commons_api(requests: list, files: dict[str, dict]) -> Client:
    """A fake Commons API: imageinfo for the files it has, `missing` for the rest,
    and underscores normalized to spaces like MediaWiki does."""

    def handler(request):
        requests.append(request)
        query: dict = {"pages": [], "normalized": []}
        for title in request.url.params["titles"].split("|"):
            canonical = title.replace("_", " ")
            if canonical != title:
                query["normalized"].append({"from": title, "to": canonical})
            info = files.get(canonical)
            query["pages"].append({"title": canonical, **({"imageinfo": [info]} if info else {"missing": True})})
        return httpx.Response(200, json={"batchcomplete": True, "query": query})

    return Client("https://example.org", transport=httpx.MockTransport(handler), min_interval=0)


def test_commons_info_asks_only_for_titles_no_snapshot_answers(tmp_path):
    raw, lock_path, requests = tmp_path / "raw", tmp_path / "sources.lock.json", []
    files = {"File:De-Hand.ogg": {"url": "hand"}, "File:De-gut 2.ogg": {"url": "gut"}}
    quiet = {"log": lambda message: None}
    with commons_api(requests, files) as client:
        first = commons.info(["De-Hand.ogg", "De-gut_2.ogg", "Gone.ogg"], raw, lock_path, client, **quiet)
        again = commons.info(["Gone.ogg", "De-gut_2.ogg", "De-Hand.ogg"], raw, lock_path, client, **quiet)
        shifted = commons.info(["De-Hand.ogg", "De-Tag.ogg"], raw, lock_path, client, **quiet)
    assert first == again == {"De-Hand.ogg": {"url": "hand"}, "De-gut_2.ogg": {"url": "gut"}}
    assert shifted == {"De-Hand.ogg": {"url": "hand"}}
    # A missing file is an answer too; a new list only asks for its new title.
    assert [r.url.params["titles"] for r in requests] == [
        "File:De-Hand.ogg|File:De-gut_2.ogg|File:Gone.ogg",
        "File:De-Tag.ogg",
    ]
    assert sorted(lock.load(lock_path)) == sorted(
        p.relative_to(raw).as_posix() for p in (raw / "commons" / "info").iterdir()
    )
