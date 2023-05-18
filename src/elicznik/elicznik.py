#!/usr/bin/env python3

import csv
import datetime

from .session import Session


class ELicznik:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    DATA_URL = "https://elicznik.tauron-dystrybucja.pl/energia/do/dane"

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

    def get_raw_data(self, start_date, end_date=None):
        end_date = end_date or start_date
        return self.session.post(
            self.DATA_URL,
            data={
                "form[from]": start_date.strftime("%d.%m.%Y"),
                "form[to]": end_date.strftime("%d.%m.%Y"),
                "form[type]": "godzin",  # or "dzien"
                "form[consum]": 1,
                "form[oze]": 1,
                "form[fileType]": "CSV",  # or "XLS"
            },
        ).text.splitlines()

    @staticmethod
    def parse_timestamp(timespec):
        date, time = timespec.split(None, 1)
        hour = int(time.split(":")[0]) - 1
        return datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(
            hours=hour
        )

    def get_readings(self, start_date, end_date=None):
        end_date = end_date or start_date
        data = self.get_raw_data(start_date, end_date)

        records = [
            {
                "timestamp": self.parse_timestamp(rec["Data"]),
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
            rec["timestamp"]: rec["value"] for rec in records if rec["type"] == "pobór"
        }
        cons = {
            rec["timestamp"]: rec["value"]
            for rec in records
            if rec["type"] == "oddanie"
        }

        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            (timestamp, cons.get(timestamp), prod.get(timestamp))
            for timestamp in set(cons) | set(prod)
        )
