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
