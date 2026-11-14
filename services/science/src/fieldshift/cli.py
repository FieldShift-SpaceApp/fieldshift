"""Command-line entry point (`fieldshift`). Subcommands are added by the pipeline stories."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from fieldshift import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fieldshift", description="FieldShift science pipeline")
    parser.add_argument("--version", action="version", version=f"fieldshift {__version__}")
    sub = parser.add_subparsers(dest="command")

    contracts = sub.add_parser("contracts", help="data contracts (ADR-4)")
    contracts_sub = contracts.add_subparsers(dest="contracts_command", required=True)
    export = contracts_sub.add_parser(
        "export", help="write packages/contracts/schema/contracts.schema.json"
    )
    export.add_argument("--out", type=Path, default=None, help="output path (default: repo)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "contracts" and args.contracts_command == "export":
        from fieldshift.contracts.export import export

        path = export(args.out)
        print(f"contracts schema written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
