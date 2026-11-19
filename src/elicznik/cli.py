"""Command line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from . import __version__
from .client import Client
from .config import load_credentials
from .errors import ConfigError, ElicznikError
from .output import WRITERS, write_atomic

_LOGGER = logging.getLogger("elicznik")


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}, expected YYYY-MM-DD") from None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="elicznik",
        description="Download hourly energy readings from Tauron eLicznik.",
        epilog="Credentials are read from ELICZNIK_USERNAME / ELICZNIK_PASSWORD / ELICZNIK_SITE, "
        "the environment or a .env file. Exit codes: 0 ok, 1 error, 2 config, 3 auth, "
        "4 rate limited, 5 bad response.",
    )
    p.add_argument("start", nargs="?", type=_parse_date, help="first local day, YYYY-MM-DD (default: yesterday)")
    p.add_argument("end", nargs="?", type=_parse_date, help="last local day, inclusive (default: START)")
    p.add_argument("--days", type=int, metavar="N", help="last N days ending yesterday (instead of START/END)")
    p.add_argument("-f", "--format", choices=WRITERS, default="jsonl", help="output format (default: jsonl)")
    p.add_argument("-o", "--output", metavar="FILE", help="write to FILE atomically instead of stdout")
    p.add_argument("-u", "--username", help="override ELICZNIK_USERNAME")
    p.add_argument("--site", help="metering point, overrides ELICZNIK_SITE (format 123_456_789)")
    p.add_argument("--env-file", metavar="PATH", help="read credentials from PATH (default: ./.env if present)")
    verbosity = p.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true", help="debug logging on stderr")
    verbosity.add_argument("-q", "--quiet", action="store_true", help="only log errors")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _date_range(args: argparse.Namespace) -> tuple[date, date]:
    yesterday = date.today() - timedelta(days=1)
    if args.days is not None:
        if args.start or args.end:
            raise ConfigError("--days cannot be combined with START/END")
        if args.days < 1:
            raise ConfigError("--days must be at least 1")
        return yesterday - timedelta(days=args.days - 1), yesterday
    start = args.start or yesterday
    end = args.end or start
    if end < start:
        raise ConfigError("END is before START")
    return start, end


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.ERROR if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        start, end = _date_range(args)
        creds = load_credentials(username=args.username, site=args.site, env_file=args.env_file)
        _LOGGER.info("Fetching readings for %s..%s", start, end)
        with Client.from_credentials(creds) as client:
            readings = client.readings(start, end)
        _LOGGER.info("Got %d hourly readings", len(readings))

        writer = WRITERS[args.format]
        render = lambda out: writer(readings, out, start=start, end=end, site=creds.site)  # noqa: E731
        if args.output:
            write_atomic(args.output, render)
        else:
            render(sys.stdout)
    except ElicznikError as err:
        _LOGGER.error("%s", err)
        return err.exit_code
    except KeyboardInterrupt:
        return 130
    except Exception:
        _LOGGER.exception("Unexpected error")
        return 1
    return 0


def main() -> None:
    sys.exit(run())
