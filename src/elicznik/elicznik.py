#!/usr/bin/env python3

import csv
import datetime

from .session import Session

class ELicznikBase:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"

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

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ELicznikChart(ELicznikBase):
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/energia/api"

    def _get_raw_daily_readings(self, type_, date):
        data = self.session.post(
            self.CHART_URL,
            data={
                "type": type_,
                "from": date.strftime("%d.%m.%Y"),
                "to": date.strftime("%d.%m.%Y"),
                "profile": "full time",
            },
        ).json().get("data", {}).get("values", [])

        return ((datetime.datetime.combine(date, datetime.time(h)), value) for h, value in enumerate(data))

    def _get_raw_readings(self, type_, start_date, end_date=None):
        end_date = end_date or start_date
        while start_date <= end_date:
            yield from self._get_raw_daily_readings(type_, start_date)
            start_date += datetime.timedelta(days=1)

    def get_readings_production(self, start_date, end_date=None):
        return dict(self._get_raw_readings("oze", start_date, end_date))

    def get_readings_consumption(self, start_date, end_date=None):
        return dict(self._get_raw_readings("consum", start_date, end_date))

    def get_readings(self, start_date, end_date=None):
        consumed = self.get_readings_consumption(start_date, end_date)
        produced = self.get_readings_production(start_date, end_date)
        return sorted(
            (timestamp, consumed.get(timestamp), produced.get(timestamp))
            for timestamp in set(consumed) | set(produced)
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
                "form[consum]": 1,
                "form[oze]": 1,
                "form[fileType]": "CSV",  # or "XLS"
            },
        ).text.splitlines()

    @staticmethod
    def _parse_timestamp(timespec):
        date, time = timespec.split(None, 1)
        hour = int(time.split(":")[0]) - 1
        return datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(hours=hour)

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

        prod = {
            rec["timestamp"]: rec["value"]
            for rec in records
            if rec["type"] == "oddanie"
        }
        cons = {
            rec["timestamp"]: rec["value"]
            for rec in records
            if rec["type"] == "pobór"
        }

        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            (timestamp, cons.get(timestamp), prod.get(timestamp))
            for timestamp in set(cons) | set(prod)
        )

ELicznik = ELicznikCSV
