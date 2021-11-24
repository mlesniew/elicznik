import argparse
import csv
import datetime
import json
import sys

import tabulate

from .elicznik import ELicznik


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=["raw", "table", "csv"],
        default="table",
        help="Specify the output format",
    )
    parser.add_argument("username", help="tauron-dystrybucja.pl user name")
    parser.add_argument("password", help="tauron-dystrybucja.pl password")
    parser.add_argument(
        "date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=datetime.date.today() - datetime.timedelta(days=1),
        help="Date of data to be retrieved",
    )

    args = parser.parse_args()

    elicznik = ELicznik(args.username, args.password)
    elicznik.login()

    if args.format == "raw":
        print(json.dumps(elicznik.get_raw_readings(args.date), indent=4))
        return

    result = elicznik.get_readings(args.date)

    if args.format == "table":
        print(tabulate.tabulate(result, headers=["timestamp", "consumed", "produced"]))
    else:
        writer = csv.writer(sys.stdout)
        for timestamp, consumed, produced in result:
            writer.writerow((timestamp.isoformat(), consumed, produced))


if __name__ == "__main__":
    main()
