import argparse
import csv
import datetime
import getpass
import os
import sys
import re

import tabulate

from .elicznik import ELicznikChart, ELicznikCSV

SITE_ID_PATTERN = "[0-9]+_[0-9]+_[0-9]+"

def parse_site(site):
    match = re.match(SITE_ID_PATTERN, site)
    if not match:
        raise ValueError
    return match.string


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Specify the output format",
    )
    parser.add_argument(
        "--api",
        choices=["chart", "csv"],
        default="csv",
        help="Specify which Tauron API to use to get the measurements",
    )
    parser.add_argument(
        "--site",
        type=parse_site,
        default=None,
        help=f"site identifier, must match '{SITE_ID_PATTERN}'",
    )
    parser.add_argument(
        "-u",
        "--username",
        default=os.environ.get("ELICZNIK_USERNAME"),
        help="tauron-dystrybucja.pl user name "
        "(default: $ELICZNIK_USERNAME, prompted for if unset)",
    )
    parser.add_argument(
        "start_date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=datetime.date.today() - datetime.timedelta(days=1),
        help="Start date of date range to be retrieved, in ISO8601 format. "
        "If the end date is omitted, it's the only date for which "
        "measurements are retrieved.",
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=None,
        help="End date of date range to be retrieved, inclusive, "
        "in ISO8601 format.  Can be omitted to only retrieve a single "
        "day's measurements.",
    )

    args = parser.parse_args()

    # The password is deliberately not accepted as a command line argument,
    # because that would leak it to shell history and process listings.
    username = args.username
    if not username:
        print("Username: ", end="", file=sys.stderr, flush=True)
        username = input()
    password = os.environ.get("ELICZNIK_PASSWORD") or getpass.getpass()

    elicznik_class = ELicznikCSV if args.api == "csv" else ELicznikChart

    with elicznik_class(username, password, args.site) as elicznik:
        result = elicznik.get_readings(args.start_date, args.end_date)

        if args.format == "table":
            print(
                tabulate.tabulate(
                    result,
                    headers=[
                        "timestamp",
                        "consumption",
                        "production",
                        "net consumption",
                        "net production",
                    ],
                )
            )
        else:
            writer = csv.writer(sys.stdout)
            for timestamp, consumed, produced, net_consumed, net_produced in result:
                writer.writerow((timestamp.isoformat(), consumed, produced, net_consumed, net_produced))


if __name__ == "__main__":
    main()
