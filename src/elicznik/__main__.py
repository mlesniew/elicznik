import argparse
import csv
import datetime
import sys

import tabulate

from .elicznik import ELicznik


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Specify the output format",
    )
    parser.add_argument("username", help="tauron-dystrybucja.pl user name")
    parser.add_argument("password", help="tauron-dystrybucja.pl password")
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

    with ELicznik(args.username, args.password) as elicznik:
        result = elicznik.get_readings(args.start_date, args.end_date)

        if args.format == "table":
            print(
                tabulate.tabulate(result, headers=["timestamp", "consumed", "produced"])
            )
        else:
            writer = csv.writer(sys.stdout)
            for timestamp, consumed, produced in result:
                writer.writerow((timestamp.isoformat(), consumed, produced))


if __name__ == "__main__":
    main()
