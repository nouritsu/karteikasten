"""Polite HTTP for every upstream.

Each request carries an identifying User-Agent with a contact, each host gets at
most one request per `min_interval` (0.5 s: Wikimedia's 2 requests per second),
and transient failures are retried with exponential backoff that honours
Retry-After. Downloads stream to a .part file, resume it when the server allows
ranges, and only replace the destination once complete.
"""

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from karteikasten_pipeline import __version__

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_BACKOFF = 60.0
CHUNK = 1 << 20


def user_agent(contact: str) -> str:
    return f"karteikasten-pipeline/{__version__} ({contact}) python-httpx/{httpx.__version__}"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Download:
    url: str
    bytes: int
    sha256: str


class FetchError(Exception):
    pass


class Client:
    def __init__(
        self,
        contact: str,
        *,
        min_interval: float = 0.5,
        attempts: int = 5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._http = httpx.Client(
            headers={"User-Agent": user_agent(contact)},
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, read=300.0),
            transport=transport,
        )
        self._min_interval = min_interval
        self._attempts = attempts
        self._sleep = sleep
        self._clock = clock
        self._last_request: dict[str, float] = {}

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._http.close()

    def get_json(self, url: str, params: dict[str, str] | None = None) -> Any:
        for attempt in range(1, self._attempts + 1):
            self._wait_turn(url)
            try:
                response = self._http.get(url, params=params)
            except httpx.TransportError as error:
                self._back_off(attempt, url, str(error))
                continue
            if response.status_code in RETRY_STATUSES:
                self._back_off(attempt, url, f"HTTP {response.status_code}", response)
                continue
            response.raise_for_status()
            return response.json()
        raise AssertionError("unreachable: _back_off raises on the last attempt")

    def download(self, url: str, dest: Path) -> Download:
        part = dest.with_name(dest.name + ".part")
        dest.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, self._attempts + 1):
            offset = part.stat().st_size if part.exists() else 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            self._wait_turn(url)
            try:
                with self._http.stream("GET", url, headers=headers) as response:
                    if response.status_code == 416:
                        part.unlink()
                        continue
                    if response.status_code in RETRY_STATUSES:
                        self._back_off(attempt, url, f"HTTP {response.status_code}", response)
                        continue
                    response.raise_for_status()
                    resumed = offset > 0 and response.status_code == 206
                    with part.open("ab" if resumed else "wb") as out:
                        for chunk in response.iter_bytes(CHUNK):
                            out.write(chunk)
            except httpx.TransportError as error:
                self._back_off(attempt, url, str(error))
                continue
            size = part.stat().st_size
            digest = sha256_of(part)
            part.replace(dest)
            return Download(url=url, bytes=size, sha256=digest)
        raise FetchError(f"{url}: giving up after {self._attempts} attempts")

    def _wait_turn(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        last = self._last_request.get(host)
        if last is not None:
            delay = self._min_interval - (self._clock() - last)
            if delay > 0:
                self._sleep(delay)
        self._last_request[host] = self._clock()

    def _back_off(self, attempt: int, url: str, reason: str, response: httpx.Response | None = None) -> None:
        if attempt == self._attempts:
            raise FetchError(f"{url}: giving up after {attempt} attempts ({reason})")
        delay = min(2.0 ** (attempt - 1), MAX_BACKOFF)
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after is not None and retry_after.isdigit():
            delay = min(float(retry_after), MAX_BACKOFF)
        self._sleep(delay)
