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


@pytest.mark.parametrize(
    "argv",
    [
        ["build", "--profile", "public"],
        ["report"],
    ],
)
def test_stub_commands_report_their_checkout(tmp_path, monkeypatch, capsys, argv):
    root = checkout(tmp_path)
    monkeypatch.chdir(root)
    assert main(argv) == 0
    output = capsys.readouterr().out
    assert "TODO" in output
    assert str(root) in output


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
