import datetime
import configparser
import elicznik
import csv
from collections import defaultdict
import os
from glob import glob

# read config file
config = configparser.ConfigParser()
config.read(['config.ini','config-local.ini'])

username = config['ACCOUNT']['USERNAME']
password = config['ACCOUNT']['PASSWORD']
meter_id = config['ACCOUNT']['METER_ID']

start_date = datetime.date(2020, 10, 12)
end_date = datetime.date.today()-datetime.timedelta(days=1)

datadir='data'

data = defaultdict(dict)
miss = []
ts = end_date
while ts > start_date:
    try :
        with open(f'{datadir}/{ts.year}/{ts.month:02d}/{ts.year}_{ts.month:02d}_{ts.day:02d}.csv') as f:
            if len(f.readlines()) < 23:
                # The DST change days are 23 hours
                miss.append(ts)
                # print(ts)
    except FileNotFoundError:
        miss.append(ts)
        # print(ts)

    ts = ts-datetime.timedelta(days=1)

if miss:
    with elicznik.ELicznik(username, password) as m:
        # date range
        print("Reading data:")

        for mts in sorted(miss):
            print(mts)
            readings = m.get_data(mts)
            for ts, consumed, produced, netconsum, netprod in readings:
                if consumed is not None or produced is not None:
                    data[mts.strftime("%Y.%m.%d")][ts]=(consumed, produced)
                # print(ts, consumed, produced)
if data:
    print('Writing data')
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
            print(f'{datadir}/{y}/{m}/{y}_{m}_{d}.csv')
            wrt = csv.writer(of)
            for t, (c, p) in sorted(data[k].items()):
                wrt.writerow([t, c, p])
