"""Stage 10: snapshot every source into data/raw and record each file in sources.lock.json.

Without --refresh, a file that is on disk and in the lock is left alone. A refresh
that yields identical bytes keeps the old lock entry, so the lock only changes
when the data does.
"""

from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

from karteikasten_pipeline.fetch import lock
from karteikasten_pipeline.fetch.http import Client, sha256_of
from karteikasten_pipeline.fetch.sources import SOURCES, Source


def utc_timestamp(when: datetime) -> str:
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot(client: Client, raw: Path, lock_path: Path, relative: str, url: str, source: str) -> Path:
    """One per-item file (a Commons recording, an ARASAAC pictogram) into data/raw, recorded
    in the lock like any other snapshot; an existing locked file is reused."""
    dest = raw / relative
    entries = lock.load(lock_path)
    if dest.exists() and relative in entries:
        return dest
    download = client.download(url, dest)
    entries[relative] = lock.Entry(
        source=source,
        url=url,
        retrieved_at=utc_timestamp(datetime.now(UTC)),
        bytes=download.bytes,
        sha256=download.sha256,
    )
    lock.save(lock_path, entries)
    return dest


def run(
    raw: Path,
    lock_path: Path,
    client: Client,
    *,
    sources: Iterable[Source] = SOURCES,
    refresh: bool = False,
    log: Callable[[str], None] = print,
) -> None:
    entries = lock.load(lock_path)
    for source in sources:
        for file in source.files:
            dest = raw / file.path
            known = entries.get(file.path)

            if source.manual:
                if not dest.exists():
                    log(f"{file.path}: missing. {source.manual}")
                elif known is None or known.bytes != dest.stat().st_size:
                    mtime = datetime.fromtimestamp(dest.stat().st_mtime, UTC)
                    entries[file.path] = lock.Entry(
                        source=source.id,
                        url=file.url,
                        retrieved_at=utc_timestamp(mtime),
                        bytes=dest.stat().st_size,
                        sha256=sha256_of(dest),
                    )
                    lock.save(lock_path, entries)
                    log(f"{file.path}: recorded (placed by hand)")
                continue

            if dest.exists() and known is not None and not refresh:
                log(f"{file.path}: have it, retrieved {known.retrieved_at}")
                continue

            log(f"{file.path}: downloading {file.url}")
            download = client.download(file.url, dest)
            if known is not None and known.sha256 == download.sha256:
                log(f"{file.path}: unchanged")
                continue
            entries[file.path] = lock.Entry(
                source=source.id,
                url=file.url,
                retrieved_at=utc_timestamp(datetime.now(UTC)),
                bytes=download.bytes,
                sha256=download.sha256,
            )
            lock.save(lock_path, entries)
            log(f"{file.path}: {download.bytes:,} bytes, sha256 {download.sha256[:12]}")
