# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Command-line entry point (`fieldshift`). Subcommands are added by the pipeline stories."""

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from fieldshift import __version__


def _iso_date(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text!r}") from exc


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

    fetch = sub.add_parser("fetch", help="fetch a source into data/cache and write site outputs")
    fetch_sub = fetch.add_subparsers(dest="source", required=True)
    pw = fetch_sub.add_parser(
        "power",
        help="NASA POWER daily (community AG) -> monthly series + provenance",
        description=(
            "Site coordinates come from data/sites/<id>/input/site.yaml, from the DEV list "
            "(dev-floripa) or from --lat/--lon. DEV sites write to data/dev/<id>/output/."
        ),
    )
    pw.add_argument("--site", required=True, help="site id (e.g. dev-floripa)")
    pw.add_argument("--lat", type=float, default=None, help="latitude (overrides the site file)")
    pw.add_argument("--lon", type=float, default=None, help="longitude (overrides the site file)")
    pw.add_argument("--start", type=_iso_date, default=None, help="first day (default 1981-01-01)")
    pw.add_argument(
        "--end", type=_iso_date, default=None, help="last day (default: end of last month, BRT)"
    )
    pw.add_argument("--offline", action="store_true", help="use data/cache only; never the network")
    pw.add_argument("--refresh", action="store_true", help="ignore the cache and download again")
    pw.add_argument("--data-dir", type=Path, default=None, help="data/ root (default: repo data/)")

    rot = sub.add_parser(
        "rotation",
        help="current rotation -> monthly soil-cover timeline (Story 2.3)",
        description=(
            "Reads input/site.yaml (ag_year) and input/rotation-current.yaml of the site and "
            "writes output/rotation-current.json; provenance is merged into output/provenance.json."
        ),
    )
    rot.add_argument("--site", required=True, help="site id (e.g. brasil)")
    rot.add_argument("--data-dir", type=Path, default=None, help="data/ root (default: repo data/)")
    return parser


def _rotation(args: argparse.Namespace) -> int:
    from fieldshift.config import data_dir
    from fieldshift.errors import PipelineError
    from fieldshift.rotation.stage import run_rotation

    try:
        out = run_rotation(args.site, data_dir=args.data_dir or data_dir())
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    bare = out.file.timeline.bare_months_per_year.value
    print(f"rotation {args.site}: {out.file.rotation.id} ({out.file.rotation.cycle_years} y)")
    print(f"  timeline:   {out.rotation_path} (bare-soil months per year: {bare})")
    print(f"  provenance: {out.provenance_path}")
    return 0


def _fetch_power(args: argparse.Namespace) -> int:
    from fieldshift.config import data_dir
    from fieldshift.errors import LayerError, PipelineError
    from fieldshift.pipeline import run_power
    from fieldshift.sites import resolve_site
    from fieldshift.sources.power import POWER_START, default_end

    root = args.data_dir or data_dir()
    start = args.start or POWER_START
    end = args.end or default_end()
    try:
        site = resolve_site(args.site, root, lat=args.lat, lon=args.lon)
        if end < start:
            raise PipelineError(f"--end {end} is before --start {start}")
        out = run_power(site, data_dir=root, start=start, end=end, offline=args.offline,
                        refresh=args.refresh)  # fmt: skip
    except (LayerError, PipelineError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    tag = " [DEV ONLY]" if site.dev else ""
    print(f"NASA POWER{tag} {site.id} ({site.lat}, {site.lon}) {start}..{end}")
    print(f"  series:     {out.series_path} ({len(out.bundle.series)} series)")
    print(f"  provenance: {out.provenance_path} ({len(out.registry.records)} records)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "contracts" and args.contracts_command == "export":
        from fieldshift.contracts.export import export

        path = export(args.out)
        print(f"contracts schema written: {path}")
    elif args.command == "fetch" and args.source == "power":
        return _fetch_power(args)
    elif args.command == "rotation":
        return _rotation(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
