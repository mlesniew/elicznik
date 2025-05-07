import datetime
import configparser
import elicznik
import csv
from collections import defaultdict
import os

# read config file
config = configparser.ConfigParser()
config.read(['config.ini','config-local.ini'])

username = config['ACCOUNT']['USERNAME']
password = config['ACCOUNT']['PASSWORD']
meter_id = config['ACCOUNT']['METER_ID']

start_date = datetime.date(2020, 10, 12)
end_date = datetime.date.today()

datadir='data'

ts = end_date
data = defaultdict(dict)

with elicznik.ELicznik(username, password) as m:
    # date range
    print("Reading data:")

    # The data is provided in one month chunks

    tsf = end_date
    while tsf > start_date:
        tsi = tsf-datetime.timedelta(weeks=4)
        print(f'{tsi} -> {tsf}')

        readings = m.get_readings(tsi, tsf)

        for ts, consumed, produced, netcons, netprod in readings:
            data[ts.strftime("%Y.%m.%d")][ts]=(consumed, produced)
            # print(ts, consumed, produced)

        tsf = tsi-datetime.timedelta(days=1)

for k in sorted(data):
    y, m, d = k.split('.')
    try :
        os.mkdir(f'{datadir}/{y}')
    except FileExistsError:
        pass
    try :
        os.mkdir(f'{datadir}/{y}/{m}')
    except FileExistsError:
        pass
    with open(f'{datadir}/{y}/{m}/{y}_{m}_{d}.csv', 'wt') as of :
        wrt = csv.writer(of)
        for t, (c, p) in sorted(data[k].items()):
            wrt.writerow([t, c, p])
