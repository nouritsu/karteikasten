"""Stage 50: audio candidates per word.

Audio comes from the Commons files both Wiktionary editions link. Preference
(D24): the author who covers most of the deck, then authors with less and less
coverage, so each word keeps the most common voice available; regional files
(Austria, Switzerland) only after every standard one, and tagged. A file needs
an author and a licence to be picked, and the public profile skips NC/ND files.
Own recordings in overrides/audio always win.
"""

import html
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REGION_PREFIX = {"De-at-": "Austria", "De-ch-": "Switzerland"}
REGION_TAGS = {"Austria": "Austria", "Switzerland": "Switzerland", "Swiss": "Switzerland", "Southern-Germany": "Bavaria"}
# Artist values that name nobody: such files rank after every named author.
ANONYMOUS = {"", "own work", "myself", "self", "unknown"}
NON_FREE = re.compile(r"\b(?:NC|ND)\b")


@dataclass(frozen=True)
class AudioCandidate:
    file: str  # Commons file name
    region: str | None  # None means Germany or untagged standard German
    germany: bool  # explicitly tagged Germany


def audio_candidates(entries: Iterable[dict]) -> list[AudioCandidate]:
    found: dict[str, AudioCandidate] = {}
    for entry in entries:
        for sound in entry.get("sounds", []):
            file = sound.get("audio")
            if not file:
                continue
            tags = set(sound.get("tags", []))
            region = next((REGION_TAGS[t] for t in tags if t in REGION_TAGS), None)
            region = region or next((r for prefix, r in REGION_PREFIX.items() if file.startswith(prefix)), None)
            candidate = AudioCandidate(file=file, region=region, germany="Germany" in tags)
            known = found.get(file)
            if known is None or (candidate.germany and not known.germany) or (candidate.region and not known.region):
                found[file] = candidate
    return sorted(found.values(), key=lambda c: c.file)


def plain(value: str | None) -> str:
    """Text of an HTML value from the Commons API."""
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def metadata(info: dict, field: str) -> str:
    """One extmetadata field of a file's imageinfo, as plain text."""
    return plain(info.get("extmetadata", {}).get(field, {}).get("value"))


def author(info: dict) -> str | None:
    """Who recorded a file, as a key for grouping files by voice: the first linked
    name in its Artist field (Lingua Libre lists the speaker first), else the
    field's text, case-folded and without a User: prefix; None when it names
    nobody. Credits use the whole Artist field."""
    artist = info.get("extmetadata", {}).get("Artist", {}).get("value") or ""
    link = re.search(r"<a\b[^>]*>(.*?)</a>", artist, re.DOTALL)
    name = re.sub(r"^(?:user|benutzer):", "", plain(link.group(1) if link else artist).casefold())
    return None if name in ANONYMOUS else name


def usable(info: dict | None, profile: str) -> bool:
    """A file can ship when Commons names its author and licence; public builds skip NC/ND."""
    if not info or not metadata(info, "Artist"):
        return False
    licence = metadata(info, "LicenseShortName")
    return bool(licence) and (profile != "public" or not NON_FREE.search(licence))


def author_coverage(candidates: dict[str, list[AudioCandidate]], infos: dict[str, dict], profile: str) -> dict[str, int]:
    """Author -> number of deck words with a usable standard-German file by them."""
    words: dict[str, set[str]] = defaultdict(set)
    for word, cands in candidates.items():
        for c in cands:
            info = infos.get(c.file)
            if c.region is None and usable(info, profile) and (who := author(info)):
                words[who].add(word)
    return {who: len(ids) for who, ids in words.items()}


def pick_audio(
    candidates: list[AudioCandidate], infos: dict[str, dict], coverage: dict[str, int], profile: str
) -> AudioCandidate | None:
    """D24: standard files before regional ones; among those, the author covering most
    of the deck first and anonymous files last; then Germany-tagged, then file name."""

    def rank(c: AudioCandidate) -> tuple[bool, int, str, bool, str]:
        who = author(infos[c.file])
        return c.region is not None, -coverage.get(who, 0) if who else 1, who or "", not c.germany, c.file

    return min((c for c in candidates if usable(infos.get(c.file), profile)), key=rank, default=None)


# -- processing -----------------------------------------------------------------------------
# Deterministic: same input and tool versions give the same bytes (bit-exact flags,
# metadata stripped), and files are named by the SHA-1 of what they contain.

AUDIO_FILTER = ",".join(
    [
        "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB:detection=peak",
        "areverse",
        "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB:detection=peak",
        "areverse",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
    ]
)


def _store(data: bytes, directory: Path, suffix: str) -> str:
    import hashlib

    name = hashlib.sha1(data).hexdigest() + suffix
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if not target.exists():
        target.write_bytes(data)
    return name


def process_audio(source: Path, directory: Path) -> tuple[str, int]:
    """Silence trimmed to 100 ms each side, about -16 LUFS, mono MP3 at 48 kbps.
    Returns (file name, duration in ms)."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.mp3"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(source), "-af", AUDIO_FILTER,
             "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "48k",
             "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out)],
            check=True,
        )
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out)],
            check=True, capture_output=True, text=True,
        )
        return _store(out.read_bytes(), directory, ".mp3"), round(float(probe.stdout.strip()) * 1000)

