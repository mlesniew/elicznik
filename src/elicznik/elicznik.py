#!/usr/bin/env python3

import collections
import csv
import datetime

from .session import Session


Reading = collections.namedtuple("Reading", "timestamp consumption production net_consumption net_production")


class ELicznikBase:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"

    def __init__(self, username, password, site=None):
        self.username = username
        self.password = password
        self.site = site

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
        if self.site is not None:
            self.session.post(
                "https://elicznik.tauron-dystrybucja.pl/ustaw_punkt",
                data={
                    "site[client]": self.site
                },
            )

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ELicznikChart(ELicznikBase):
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/energia/api"

    def _get_raw_daily_readings(self, type_, date):
        data = (
            self.session.post(
                self.CHART_URL,
                data={
                    "type": type_,
                    "from": date.strftime("%d.%m.%Y"),
                    "to": date.strftime("%d.%m.%Y"),
                    "profile": "full time",
                },
            )
            .json()
            .get("data", {})
            .get("values", [])
        )

        return (
            (datetime.datetime.combine(date, datetime.time(h)), value)
            for h, value in enumerate(data)
        )

    def _get_raw_readings(self, type_, start_date, end_date=None):
        end_date = end_date or start_date
        while start_date <= end_date:
            yield from self._get_raw_daily_readings(type_, start_date)
            start_date += datetime.timedelta(days=1)

    def get_readings(self, start_date, end_date=None):
        COLUMNS = ["consum", "oze", "netto", "netto_oze"]

        results = {
            name: dict(self._get_raw_readings(name, start_date, end_date))
            for name in COLUMNS
        }

        timestamps = set(sum((list(v) for v in results.values()), start=[]))

        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            Reading(*([timestamp] + [results[name].get(timestamp) for name in COLUMNS]))
            for timestamp in timestamps
        )


class ELicznikCSV(ELicznikBase):
    DATA_URL = "https://elicznik.tauron-dystrybucja.pl/energia/do/dane"

    def _get_raw_data(self, start_date, end_date=None):
        end_date = end_date or start_date
        return self.session.get(
            self.DATA_URL,
            params={
                "form[from]": start_date.strftime("%d.%m.%Y"),
                "form[to]": end_date.strftime("%d.%m.%Y"),
                "form[type]": "godzin",  # or "dzien"
                "form[energy][consum]": 1,
                "form[energy][oze]": 1,
                "form[energy][netto]": 1,
                "form[energy][netto_oze]": 1,
                "form[fileType]": "CSV",  # or "XLS"
            },
        ).text.splitlines()

    @staticmethod
    def _parse_timestamp(timespec):
        date, time = timespec.split(None, 1)
        hour = int(time.split(":")[0]) - 1
        return datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(
            hours=hour
        )

    def get_readings(self, start_date, end_date=None):
        end_date = end_date or start_date
        data = self._get_raw_data(start_date, end_date)

        records = [
            {
                "timestamp": self._parse_timestamp(rec["Data"]),
                "value": float(rec[" Wartość kWh"].replace(",", ".")),
                "type": rec["Rodzaj"],
            }
            for rec in csv.DictReader(data, delimiter=";")
        ]

        # skip records which are outside the requested date range
        # TODO: is this really needed?
        records = [
            rec for rec in records if start_date <= rec["timestamp"].date() <= end_date
        ]

        COLUMNS = [
            "pobór",
            "oddanie",
            "pobrana po zbilansowaniu",
            "oddana po zbilansowaniu",
        ]

        results = {
            name: {
                rec["timestamp"]: rec["value"] for rec in records if rec["type"] == name
            }
            for name in COLUMNS
        }

        timestamps = set(sum((list(v) for v in results.values()), start=[]))

        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            Reading(*([timestamp] + [results[name].get(timestamp) for name in COLUMNS]))
            for timestamp in timestamps
        )


ELicznik = ELicznikCSV
