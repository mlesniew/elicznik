import datetime
import configparser
import elicznik

# read config file
config = configparser.ConfigParser()
config.read(['config.ini','config-local.ini'])

username = config['ACCOUNT']['USERNAME']
password = config['ACCOUNT']['PASSWORD']
meter_id = config['ACCOUNT']['METER_ID']

with elicznik.ELicznik(username, password) as m:
    # date range
    print("July 2021")

    readings = m.get_readings(datetime.date(2022, 7, 1), datetime.date(2022, 7, 2))

    for timestamp, consumed, produced, netcons, netprod in readings:
        print(timestamp, consumed, produced, netcons, netprod)

    # for l in readings.split('\n'):
    #     # timestamp, consumed, produced = split
    #     # print(timestamp, consumed, produced)
    #     print(l.split(';'))

    # single day
    print("Day before yesterday")

    yesterday = datetime.date.today() - datetime.timedelta(days=2)
    readings = m.get_readings(yesterday)

    for timestamp, consumed, produced, netcons, netprod in readings:
        print(timestamp, consumed, produced, netcons, netprod)
