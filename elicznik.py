#!/usr/bin/env python3

from urllib3 import poolmanager
import argparse
import datetime
import ssl

import requests


LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
CHART_URL = "https://elicznik.tauron-dystrybucja.pl/index/charts"


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("meter_id")

    args = parser.parse_args()

    session = Session()

    resp = session.get(LOGIN_URL)
    resp = session.post(
        LOGIN_URL,
        data={
            "username": args.username,
            "password": args.password,
            "service": "https://elicznik.tauron-dystrybucja.pl",
        },
    )

    resp = session.post(
        CHART_URL,
        data={
            # change timedelta to get data from another days (1 for yesterday)
            "dane[chartDay]": (datetime.datetime.now() - datetime.timedelta(1)).strftime("%d.%m.%Y"),
            "dane[paramType]": "day",
            "dane[smartNr]": args.meter_id,
            # comment if don't want generated energy data in JSON output:
            "dane[checkOZE]": "on",
        },
    )
    print(resp.text)


if __name__ == "__main__":
    main()
