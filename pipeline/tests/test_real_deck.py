"""Checks on the full deck in data/dist, where one has been built; skipped otherwise
(the Nix sandbox never has data/). Ranks only make sense on the whole snapshot."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "data" / "dist" / "deck" / "latest.json"


def _deck():
    if not LATEST.exists():
        return None
    version = json.loads(LATEST.read_text())["version"]
    manifest = json.loads((LATEST.parent / version / "manifest.json").read_text())
    if manifest["n_max"] < 2000 or version.endswith(("-spike", "-fixtures")):
        return None
    return {w["id"]: w for w in json.loads((LATEST.parent / version / "words.json").read_text())}


DECK = _deck()
pytestmark = pytest.mark.skipif(DECK is None, reason="no full deck in data/dist (run nix run .#build)")


@pytest.mark.parametrize("verb", ["anfangen", "aufhören", "ankommen", "anrufen"])
def test_separable_verbs_land_at_plausible_ranks(verb):
    assert DECK[f"{verb}#verb#1"]["rank"] < 1000


def test_function_words_lead():
    top = sorted(DECK.values(), key=lambda w: w["rank"])[:5]
    assert {"der#article#1", "sein#verb#1"} <= {w["id"] for w in top}


def test_every_item_is_credited():
    for w in DECK.values():
        for item in ([w["audio"]] if w["audio"] else []) + w["sentences"]:
            assert item["author"] and item["license"], (w["id"], item)
