#!/usr/bin/env python3

import datetime

from .session import Session


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
                "dane[paramType]": "csv",
                "dane[trybCSV]": "godzin",
                "dane[startDay]": start_date.strftime("%d.%m.%Y"),
                "dane[endDay]": end_date.strftime("%d.%m.%Y"),
                "dane[checkOZE]": "on",
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
