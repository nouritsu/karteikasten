from pathlib import Path

import pytest

from karteikasten_pipeline.cli import main
from karteikasten_pipeline.paths import NotInWorkingTree, find_root


def checkout(path: Path) -> Path:
    (path / "config").mkdir()
    (path / "config" / "pipeline.toml").write_text("")
    return path


def test_find_root_walks_up_from_a_subdirectory(tmp_path):
    root = checkout(tmp_path)
    nested = root / "pipeline" / "tests"
    nested.mkdir(parents=True)
    assert find_root(nested) == root


def test_find_root_outside_a_checkout(tmp_path):
    with pytest.raises(NotInWorkingTree):
        find_root(tmp_path)


def test_build_without_a_snapshot_fails_cleanly(tmp_path, monkeypatch, capsys):
    root = checkout(tmp_path)
    (root / "config" / "pipeline.toml").write_text(
        'n_max = 10\nprofile = "personal"\n[frequency]\nspoken_weight = 0.7\n[http]\ncontact = "x"\n'
    )
    monkeypatch.chdir(root)
    assert main(["build", "--offline"]) == 1
    assert "nix run .#fetch" in capsys.readouterr().err


def test_report_needs_a_deck(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(checkout(tmp_path))
    assert main(["report"]) == 1
    assert "no deck yet" in capsys.readouterr().err


def test_outside_a_checkout_fails_with_a_usage_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["build"])
    assert excinfo.value.code == 2


def test_fetch_rejects_unknown_sources(tmp_path, monkeypatch):
    monkeypatch.chdir(checkout(tmp_path))
    with pytest.raises(SystemExit) as excinfo:
        main(["fetch", "--only", "nosuchsource"])
    assert excinfo.value.code == 2
