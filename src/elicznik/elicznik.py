#!/usr/bin/env python3

import datetime

from .session import Session
from collections import defaultdict

class ELicznik:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/index/charts"
    URL_ENERGY = "https://elicznik.tauron-dystrybucja.pl/energia/api"
    URL_READINGS = "https://elicznik.tauron-dystrybucja.pl/odczyty/api"
    CHART_URL = URL_ENERGY
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

    def get_raw_readings(self, start_date, end_date=None):
        end_date = end_date or start_date
        return self.session.post(
            self.CHART_URL,
            data={
                # "dane[smartNr]": "?"
                # "dane[chartDay]": date.strftime("%d.%m.%Y"),
                # "dane[paramType]": "csv",
                # "dane[trybCSV]": "godzin",
                # "dane[startDay]": start_date.strftime("%d.%m.%Y"),
                # "dane[endDay]": end_date.strftime("%d.%m.%Y"),
                # "dane[checkOZE]": "on",
                "from": start_date.strftime("%d.%m.%Y"),
                "to" : end_date.strftime("%d.%m.%Y"),
                "profile": "full time",
                "type": "consum",
            },
        ).json()

    @staticmethod
    def _extract_values_with_timestamps(data):
        for element in data:
            date = element.get("Date")
            hour = int(element.get("Hour"))
            # TODO: There's also an "Extra" field, which seems to be set to be set to "T" only for the one extra hour
            # when switching from CEST to CET (e.g. 3 AM on 2021-10-31)
            timestamp = datetime.datetime.strptime(date, "%Y-%m-%d")
            timestamp += datetime.timedelta(hours=hour)
            value = element.get("EC")
            yield timestamp, value

    def get_readings(self, start_date, end_date=None):
        data = self.get_raw_readings(start_date, end_date).get("dane", {})
        consumed = dict(self._extract_values_with_timestamps(data.get("chart", [])))
        produced = dict(self._extract_values_with_timestamps(data.get("OZE", [])))
        return sorted(
            (timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
            for timestamp in set(consumed) | set(produced)
        )

    def get_raw_data(self, start_date, end_date=None):
        end_date = end_date or start_date
        return self.session.post(
            self.DATA_URL,
            data={
                "form[from]": start_date.strftime("%d.%m.%Y"),
                "form[to]" : end_date.strftime("%d.%m.%Y"),
                "form[type]": "godzin", # or "dzien"
                "form[consum]": 1,
                "form[oze]": 1,
                "form[fileType]": "CSV", # or "XLS"
            },
        ).content.decode()

    def get_data(self, start_date, end_date=None):
        raw_data = self.get_raw_data(start_date, end_date).split('\n')[1:]
        cons = defaultdict(float)
        prod = defaultdict(float)
        for l in raw_data:
            print(l)
            try:
                t, v, r = l.split(';')[:3]
            except ValueError:
                continue
            date, hour = t.split()
            h, m = hour.split(':')
            timestamp = datetime.datetime.strptime(date, "%d.%m.%Y")
            timestamp += datetime.timedelta(hours=int(h), minutes=int(m))
            if r=='pobór':
                cons[timestamp] = v
            elif r=='oddanie':
                prod[timestamp] = v
                pass
        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            (timestamp, float(cons[timestamp]), float(prod[timestamp]))
            for timestamp in set(cons) | set(prod)
        )

