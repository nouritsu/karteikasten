import hashlib

import httpx
import pytest

from karteikasten_pipeline.fetch.http import Client, FetchError, user_agent


class Recorder:
    """Fake sleep and clock: the clock only moves when someone sleeps."""

    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def clock(self) -> float:
        return self.now


def client(handler, recorder=None, **kwargs) -> Client:
    recorder = recorder or Recorder()
    return Client(
        "https://example.org/contact",
        transport=httpx.MockTransport(handler),
        sleep=recorder.sleep,
        clock=recorder.clock,
        **kwargs,
    )


def test_every_request_identifies_itself_with_the_contact():
    seen = []

    def handler(request):
        seen.append(request.headers["User-Agent"])
        return httpx.Response(200, json={})

    with client(handler) as http:
        http.get_json("https://api.example.org/x")
    assert seen == [user_agent("https://example.org/contact")]
    assert "(https://example.org/contact)" in seen[0]


def test_transient_errors_are_retried_with_exponential_backoff():
    statuses = iter([503, 502, 200])
    recorder = Recorder()

    def handler(request):
        status = next(statuses)
        return httpx.Response(status, json={"ok": True} if status == 200 else None)

    with client(handler, recorder, min_interval=0) as http:
        assert http.get_json("https://api.example.org/x") == {"ok": True}
    assert recorder.sleeps == [1.0, 2.0]


def test_retry_after_is_honoured():
    statuses = iter([429, 200])
    recorder = Recorder()

    def handler(request):
        status = next(statuses)
        return httpx.Response(status, headers={"Retry-After": "7"}, json={})

    with client(handler, recorder, min_interval=0) as http:
        http.get_json("https://api.example.org/x")
    assert recorder.sleeps == [7.0]


def test_gives_up_after_the_last_attempt():
    with client(lambda request: httpx.Response(503), min_interval=0, attempts=3) as http:
        with pytest.raises(FetchError, match="3 attempts"):
            http.get_json("https://api.example.org/x")


def test_client_errors_are_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(404)

    with client(handler, min_interval=0) as http:
        with pytest.raises(httpx.HTTPStatusError):
            http.get_json("https://api.example.org/missing")
    assert len(calls) == 1


def test_requests_to_one_host_are_spaced_out_but_hosts_are_independent():
    recorder = Recorder()
    with client(lambda request: httpx.Response(200, json={}), recorder, min_interval=0.5) as http:
        http.get_json("https://commons.example.org/a")
        http.get_json("https://other.example.org/a")
        http.get_json("https://commons.example.org/b")
    assert recorder.sleeps == [0.5]


def test_download_writes_the_file_and_its_hash(tmp_path):
    body = b"word\t42\n" * 1000
    with client(lambda request: httpx.Response(200, content=body)) as http:
        result = http.download("https://files.example.org/de.txt", tmp_path / "de.txt")
    assert (tmp_path / "de.txt").read_bytes() == body
    assert result.bytes == len(body)
    assert result.sha256 == hashlib.sha256(body).hexdigest()
    assert not (tmp_path / "de.txt.part").exists()


def test_download_resumes_a_partial_file(tmp_path):
    body = bytes(range(256)) * 64
    (tmp_path / "big.bin.part").write_bytes(body[:1000])

    def handler(request):
        assert request.headers["Range"] == "bytes=1000-"
        return httpx.Response(206, content=body[1000:])

    with client(handler) as http:
        result = http.download("https://files.example.org/big.bin", tmp_path / "big.bin")
    assert (tmp_path / "big.bin").read_bytes() == body
    assert result.sha256 == hashlib.sha256(body).hexdigest()


def test_download_starts_over_when_the_server_ignores_the_range(tmp_path):
    body = b"0123456789" * 100
    (tmp_path / "f.bin.part").write_bytes(b"stale bytes")

    with client(lambda request: httpx.Response(200, content=body)) as http:
        http.download("https://files.example.org/f.bin", tmp_path / "f.bin")
    assert (tmp_path / "f.bin").read_bytes() == body


def test_download_retries_a_dropped_connection(tmp_path):
    attempts = iter([httpx.ConnectError("reset"), None])

    def handler(request):
        error = next(attempts)
        if error:
            raise error
        return httpx.Response(200, content=b"done")

    with client(handler, min_interval=0) as http:
        http.download("https://files.example.org/f", tmp_path / "f")
    assert (tmp_path / "f").read_bytes() == b"done"
