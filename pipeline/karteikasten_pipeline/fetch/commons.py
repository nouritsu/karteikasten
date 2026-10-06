"""Wikimedia Commons: per-file author and licence, and the audio files themselves.

Metadata comes from the API (`imageinfo` + `extmetadata`) in batches of 50 titles,
at most 2 requests per second (the client's per-host interval), with `maxlag` so
the API can ask us to back off. Each batch response is a raw snapshot like any
other source file: data/raw/commons/info/<key>.json, recorded in sources.lock.json.
Titles are looked up across all snapshots, newest first, so only titles none of
them answers are ever requested, however the deck's file list shifts.
"""

import hashlib
import json
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from karteikasten_pipeline.fetch import lock
from karteikasten_pipeline.fetch.http import Client, sha256_of

API = "https://commons.wikimedia.org/w/api.php"
BATCH = 50
METADATA = "Artist|LicenseShortName|LicenseUrl|Credit|AttributionRequired|UsageTerms"


def batch_key(titles: list[str]) -> str:
    return hashlib.sha1("\n".join(titles).encode()).hexdigest()[:16]


def answers(data: dict) -> dict[str, dict | None]:
    """What one API response says per title it was asked about, under the name it was
    asked by: the imageinfo, or None when Commons has no such file."""
    query = data.get("query", {})
    pages = {page["title"]: (page.get("imageinfo") or [None])[0] for page in query.get("pages", [])}
    renamed = {n["from"]: n["to"] for n in query.get("normalized", []) + query.get("redirects", [])}
    result = dict(pages)
    for name in renamed:
        key = name
        while key in renamed:
            key = renamed[key]
        result[name] = pages.get(key)
    return result


def info(
    files: Iterable[str],
    raw: Path,
    lock_path: Path,
    client: Client,
    *,
    log: Callable[[str], None] = print,
) -> dict[str, dict]:
    """imageinfo per Commons file name (as Wiktionary links it), read from the snapshots,
    fetching only the titles none of them answers. Files Commons lacks are left out."""
    entries = lock.load(lock_path)
    known: dict[str, dict | None] = {}
    snapshots = sorted((entry.retrieved_at, path) for path, entry in entries.items() if path.startswith("commons/info/"))
    for _, relative in snapshots:
        known.update(answers(json.loads((raw / relative).read_text(encoding="utf-8"))))
    names = sorted(set(files))
    missing = [name for name in names if f"File:{name}" not in known]
    for start in range(0, len(missing), BATCH):
        titles = missing[start : start + BATCH]
        path = raw / "commons" / "info" / f"{batch_key(titles)}.json"
        relative = path.relative_to(raw).as_posix()
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|sha1|extmetadata",
            "iiextmetadatafilter": METADATA,
            "redirects": "1",
            "maxlag": "5",
            "titles": "|".join(f"File:{title}" for title in titles),
        }
        data = client.get_json(API, params=params)
        if "error" in data:
            raise RuntimeError(f"Commons API: {data['error'].get('code')}: {data['error'].get('info')}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        entries[relative] = lock.Entry(
            source="commons",
            url=f"{API}?titles=" + quote("|".join(titles)),
            retrieved_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            bytes=path.stat().st_size,
            sha256=sha256_of(path),
        )
        lock.save(lock_path, entries)
        log(f"{relative}: {len(titles)} titles")
        known.update(answers(data))
    return {name: found for name in names if (found := known.get(f"File:{name}"))}
