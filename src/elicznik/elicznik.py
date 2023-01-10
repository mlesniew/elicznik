#!/usr/bin/env python3

import datetime

from .session import Session


class ELicznik:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/energia/api"

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

    def _get_raw_readings(self, type_, start_date, end_date=None):
        end_date = end_date or start_date
        data = self.session.post(
            self.CHART_URL,
            data={
                "type": type_,
                "from": start_date.strftime("%d.%m.%Y"),
                "to": end_date.strftime("%d.%m.%Y"),
                "profile": "full time",
            },
        ).json()

        data = data.get("data", {}).get("allData", {})
        for element in data:
            date = element.get("Date")
            hour = int(element.get("Hour"))
            # TODO: There's also an "Extra" field, which seems to be set to be set to "T" only for the one extra hour
            # when switching from CEST to CET (e.g. 3 AM on 2021-10-31)
            timestamp = datetime.datetime.strptime(date, "%Y-%m-%d")
            timestamp += datetime.timedelta(hours=hour)
            value = element.get("EC")
            yield timestamp, value

    def get_readings_production(self, start_date, end_date=None):
        return dict(self._get_raw_readings("oze", start_date, end_date))

    def get_readings_consumption(self, start_date, end_date=None):
        return dict(self._get_raw_readings("consum", start_date, end_date))

    def get_readings(self, start_date, end_date=None):
        consumed = self.get_readings_consumption(start_date, end_date)
        produced = self.get_readings_production(start_date, end_date)
        return sorted(
            (timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
            for timestamp in set(consumed) | set(produced)
        )
