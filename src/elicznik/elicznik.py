#!/usr/bin/env python3

import datetime

from .session import Session
from collections import defaultdict
import csv

class ELicznik:
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/energia/api"
    READINGS_URL = "https://elicznik.tauron-dystrybucja.pl/odczyty/api"
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

    def get_raw_data(self, start_date, end_date=None):
        end_date = end_date or start_date
        if start_date == end_date:
            start_date -= datetime.timedelta(days=1)
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
        ).content.decode().split('\n')

    def get_data(self, start_date, end_date=None):
        end_date = end_date or start_date
        data = csv.reader(self.get_raw_data(start_date, end_date)[1:], delimiter=';')
        cons = defaultdict(float)
        prod = defaultdict(float)
        for rec in data:
            try :
                t, v, r, *_ = rec
            except ValueError:
                # print('ValueError:', rec)
                continue
            date, hour = t.split()
            h, m = hour.split(':')
            timestamp = datetime.datetime.strptime(date, "%d.%m.%Y")
            timestamp += datetime.timedelta(hours=int(h), minutes=int(m))
            # Skip records outside a single day block
            if start_date == end_date and timestamp.day != start_date.day:
                print(f'Skip {timestamp} not within {start_date}.')
                continue
            v = v.replace(',','.')
            if r=='pobór':
                cons[timestamp] = v
            elif r=='oddanie':
                prod[timestamp] = v
            else :
                print('Unknown data format:', l)
        # TODO
        # This probably drops the data from the double hour during DST change
        # Needs to be investigated and fixed
        return sorted(
            (timestamp, float(cons[timestamp]), float(prod[timestamp]))
            for timestamp in set(cons) | set(prod)
        )

