"""Command-line entry point (`fieldshift`). Subcommands are added by the pipeline stories."""

import argparse
from collections.abc import Sequence

from fieldshift import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fieldshift", description="FieldShift science pipeline")
    parser.add_argument("--version", action="version", version=f"fieldshift {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
