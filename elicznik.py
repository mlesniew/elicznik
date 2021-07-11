#!/usr/bin/env python

import requests
from requests import adapters
import ssl
from urllib3 import poolmanager
import datetime

#Add login details & meter ID here:
username = 'TAURON_USERNAME'
password = 'TAURON_PASSWORD'
meter_id = TAURON_ENERGY_METER_ID

payload = {
                'username': username,
                'password': password ,
                'service': 'https://elicznik.tauron-dystrybucja.pl'
}

LOGIN_URL = 'https://logowanie.tauron-dystrybucja.pl/login'
CHART_URL = 'https://elicznik.tauron-dystrybucja.pl/index/charts'


# Workaround for https://github.com/psf/requests/issues/4775
class TLSAdapter(adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

session = requests.session()
session.mount('https://', TLSAdapter())

p = session.get(LOGIN_URL)
p = session.post(LOGIN_URL, data=payload)


chart = {
        #change timedelta to get data from another days (1 for yesterday)
        "dane[chartDay]": (datetime.datetime.now() - datetime.timedelta(1)).strftime('%d.%m.%Y'),
        "dane[paramType]": "day",
        "dane[smartNr]": meter_id,
        #comment if don't want generated energy data in JSON output:
        "dane[checkOZE]": "on"
        }

r = session.post(CHART_URL, data=chart)
print(r.text)

#Optionally write JSON to file
#with open('file.json', 'wb') as f:
#    f.write(r.content)
