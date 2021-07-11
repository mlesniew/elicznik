#!/usr/bin/env python3

from urllib3 import poolmanager
import argparse
import csv
import datetime
import ssl
import sys

import requests
import tabulate


LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
CHART_URL = "https://elicznik.tauron-dystrybucja.pl/index/charts"


# Workaround for https://github.com/psf/requests/issues/4775
class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLS, ssl_context=ctx
        )


class Session(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mount("https://", TLSAdapter())


def get_stats(data):
    for element in data:
        timestamp = datetime.datetime.strptime(element["Date"], "%Y-%m-%d").replace(hour=int(element["Hour"]) - 1)
        timestamp += datetime.timedelta(hours=1)
        value = element.get("EC")
        yield timestamp, value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format",
                        choices=["raw", "table", "csv"],
                        default="table")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("meter_id")
    parser.add_argument("date",
                        nargs="?",
                        type=lambda arg: datetime.datetime.strptime(arg, "%d.%m.%Y").date(),
                        default=datetime.date.today() - datetime.timedelta(days=1))

    args = parser.parse_args()

    session = Session()

    resp = session.get(LOGIN_URL)
    resp = session.post(
        LOGIN_URL,
        data={
            "username": args.username,
            "password": args.password,
            "service": "https://elicznik.tauron-dystrybucja.pl",
        },
    )

    resp = session.post(
        CHART_URL,
        data={
            "dane[chartDay]": args.date.strftime("%d.%m.%Y"),
            "dane[paramType]": "day",
            "dane[smartNr]": args.meter_id,
            "dane[checkOZE]": "on",
        },
    )

    if args.format == "raw":
        print(resp.text)
        return

    data = resp.json()

    consumed = dict(get_stats(data["dane"]["chart"].values()))
    produced = dict(get_stats(data["dane"]["OZE"].values()))
    result = sorted((timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
                    for timestamp in set(consumed) | set(produced))

    if args.format == "table":
        print(tabulate.tabulate(result, headers=["timestamp", "consumed", "produced"]))
    else:
        writer = csv.writer(sys.stdout)
        for timestamp, consumed, produced in result:
            writer.writerow((timestamp.isoformat(), consumed, produced))


if __name__ == "__main__":
    main()
