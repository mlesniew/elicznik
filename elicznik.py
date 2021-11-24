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

    def __init__(self, username, password):
        self.username = username
        self.password = password

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
                # "dane[smartNr]": "?"
                # "dane[chartDay]": date.strftime("%d.%m.%Y"),
                "dane[paramType]": "csv",
                "dane[trybCSV]": "godzin",
                "dane[startDay]": date.strftime("%d.%m.%Y"),
                "dane[endDay]": date.strftime("%d.%m.%Y"),
                "dane[checkOZE]": "on",
            },
        ).json()

    @staticmethod
    def _extract_values_with_timestamps(data):
        for element in data:
            date = element.get("Date")
            hour = int(element.get("Hour"))
            value = float(element.get("EC"))
            # TODO: There's also an "Extra" field, which seems to be set to be set to "T" only for the one extra hour
            # when switching from CEST to CET (e.g. 3 AM on 2021-10-31)
            timestamp = datetime.datetime.strptime(date, "%Y-%m-%d")
            timestamp += datetime.timedelta(hours=hour)
            value = element.get("EC")
            yield timestamp, value

    def get_readings(self, date):
        data = self.get_raw_readings(date).get("dane", {})
        consumed = dict(self._extract_values_with_timestamps(data.get("chart", [])))
        produced = dict(self._extract_values_with_timestamps(data.get("OZE", [])))
        return sorted((timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
                       for timestamp in set(consumed) | set(produced))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format",
                        choices=["raw", "table", "csv"],
                        default="table",
                        help="Specify the output format")
    parser.add_argument("username",
                        help="tauron-dystrybucja.pl user name")
    parser.add_argument("password",
                        help="tauron-dystrybucja.pl password")
    parser.add_argument("date",
                        nargs="?",
                        type=lambda arg: datetime.datetime.strptime(arg, "%d.%m.%Y").date(),
                        default=datetime.date.today() - datetime.timedelta(days=1),
                        help="Date of data to be retrieved")

    args = parser.parse_args()

    elicznik = ELicznik(args.username, args.password)
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
