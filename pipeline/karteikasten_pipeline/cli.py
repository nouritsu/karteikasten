"""Command-line entry point; `nix run .#<command>` wraps each subcommand."""

import argparse
from pathlib import Path

from karteikasten_pipeline import config, fetch
from karteikasten_pipeline.fetch.http import Client
from karteikasten_pipeline.fetch.sources import BY_ID, SOURCES
from karteikasten_pipeline.paths import NotInWorkingTree, Paths, find_root

# Phase in which each remaining command gets implemented; until then it is a stub.
PLANNED = {
    "build": 3,
    "report": 1,
}


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

    commands.add_parser("report", help="write coverage and diff reports to reports/")

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

    print(f"{args.command}: TODO (Phase {PLANNED[args.command]}); checkout: {paths.root}")
    return 0
