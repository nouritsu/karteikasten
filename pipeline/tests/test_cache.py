from karteikasten_pipeline import cache


def test_computes_once_per_key_and_keeps_only_the_latest(tmp_path):
    calls = []
    store = cache.Cache(tmp_path, log=lambda m: None)

    def compute(value):
        def run():
            calls.append(value)
            return value
        return run

    assert store.get("stage", cache.digest("a"), compute(1)) == 1
    assert store.get("stage", cache.digest("a"), compute(2)) == 1
    assert store.get("stage", cache.digest("b"), compute(3)) == 3
    assert calls == [1, 3]
    assert len(list(tmp_path.glob("stage-*.pickle"))) == 1
    fresh = cache.Cache(tmp_path, fresh=True, log=lambda m: None)
    assert fresh.get("stage", cache.digest("b"), compute(4)) == 4


def test_digest_is_canonical():
    assert cache.digest({"b": 1, "a": 2}) == cache.digest({"a": 2, "b": 1})
