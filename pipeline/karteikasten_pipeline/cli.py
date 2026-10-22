"""Command-line entry point; `nix run .#<command>` wraps each subcommand."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from karteikasten_pipeline import config, fetch
from karteikasten_pipeline.fetch.http import Client
from karteikasten_pipeline.fetch.sources import BY_ID, SOURCES
from karteikasten_pipeline.paths import NotInWorkingTree, Paths, find_root


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="karteikasten-pipeline", description=__doc__)
    cli.add_argument(
        "--root",
        type=Path,
        help="checkout to work on (default: found by walking up from the current directory)",
    )
    commands = cli.add_subparsers(dest="command", required=True)

    fetch_cli = commands.add_parser("fetch", help="snapshot every source into data/raw (stage 10)")
    fetch_cli.add_argument("--refresh", action="store_true", help="download again even if a snapshot exists")
    fetch_cli.add_argument("--only", nargs="+", choices=sorted(BY_ID), metavar="SOURCE", help="limit to these sources")

    build = commands.add_parser("build", help="build the deck bundle from data/raw (stages 20-70)")
    build.add_argument(
        "--profile",
        choices=["personal", "public"],
        help="licence profile; public drops NC/ND items (default: from config/pipeline.toml)",
    )
    build.add_argument("--fresh", action="store_true", help="recompute every stage and audio file, ignoring caches")
    build.add_argument(
        "--offline", action="store_true", help="fail instead of fetching Commons data the snapshot lacks"
    )

    commands.add_parser("report", help="copy the latest deck's coverage report to reports/coverage.md")

    return cli


def main(argv: list[str] | None = None) -> int:
    cli = parser()
    args = cli.parse_args(argv)
    try:
        paths = Paths(find_root(args.root or Path.cwd()))
    except NotInWorkingTree as error:
        cli.error(str(error))

    if args.command == "fetch":
        settings = config.load(paths.config)
        sources = [BY_ID[name] for name in args.only] if args.only else SOURCES
        with Client(settings.contact) as client:
            fetch.run(paths.raw, paths.lock, client, sources=sources, refresh=args.refresh)
        return 0

    if args.command == "build":
        from karteikasten_pipeline import build, overrides

        def log(message: str) -> None:
            print(message, file=sys.stderr, flush=True)

        try:
            dest = build.run(paths, profile=args.profile, fresh=args.fresh, offline=args.offline, log=log)
        except (build.BuildError, overrides.OverrideError) as error:
            print(f"build failed: {error}", file=sys.stderr)
            return 1
        print(dest)
        return 0

    latest = paths.dist / "deck" / "latest.json"
    if not latest.exists():
        print("report: no deck yet; run `nix run .#build` first", file=sys.stderr)
        return 1
    version = json.loads(latest.read_text(encoding="utf-8"))["version"]
    paths.reports.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(paths.dist / "deck" / version / "coverage.md", paths.reports / "coverage.md")
    print(paths.reports / "coverage.md")
    return 0
