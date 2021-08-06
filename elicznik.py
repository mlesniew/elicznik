#!/usr/bin/env python3

from urllib3 import poolmanager
import argparse
import csv
import datetime
import json
import ssl
import sys

import requests
import tabulate


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


class ELicznik:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/index/charts"

    def __init__(self, username, password, meter_id):
        self.username = username
        self.password = password
        self.meter_id = meter_id

    def login(self):
        self.session = Session()
        self.session.get(self.LOGIN_URL)
        self.session.post(
            self.LOGIN_URL,
            data={
                "username": self.username,
                "password": self.password,
                "service": "https://elicznik.tauron-dystrybucja.pl",
            },
        )

    def get_raw_readings(self, date):
        return self.session.post(
            self.CHART_URL,
            data={
                "dane[chartDay]": date.strftime("%d.%m.%Y"),
                "dane[paramType]": "day",
                "dane[smartNr]": self.meter_id,
                "dane[checkOZE]": "on",
            },
        ).json()

    @staticmethod
    def _extract_values_with_timestamps(data):
        for element in data:
            timestamp = datetime.datetime.strptime(element["Date"], "%Y-%m-%d").replace(hour=int(element["Hour"]) - 1)
            timestamp += datetime.timedelta(hours=1)
            value = element.get("EC")
            yield timestamp, value

    def get_readings(self, date):
        data = self.get_raw_readings(date)
        consumed = dict(self._extract_values_with_timestamps(data["dane"]["chart"].values()))
        produced = dict(self._extract_values_with_timestamps(data["dane"]["OZE"].values()))
        return sorted((timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
                       for timestamp in set(consumed) | set(produced))


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

    elicznik = ELicznik(args.username, args.password, args.meter_id)
    elicznik.login()

    if args.format == "raw":
        print(elicznik.get_raw_readings(args.date))
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
