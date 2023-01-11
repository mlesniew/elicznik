import datetime
import configparser
import elicznik
import pandas as pd

# read config file
config = configparser.ConfigParser()
config.read(['config.ini','config-local.ini'])

username = config['ACCOUNT']['USERNAME']
password = config['ACCOUNT']['PASSWORD']
meter_id = config['ACCOUNT']['METER_ID']

with elicznik.ELicznik(username, password) as m:
    # date range
    start = datetime.date(2020, 10, 8)
    
    end = datetime.date.today() - datetime.timedelta(days=1)
    rng = (end - start).days

    print(f'Get data from: {start} - {end} ({rng} days)')

    readings = []
    zs = start
    while zs < end:
        ze = zs + datetime.timedelta(days=60)
        if ze > end:
            ze = end
        print(f'Getting data from: {zs} - {ze} ({(ze-zs).days} days)')
        readings += m.get_readings(zs, ze)
        zs = ze + datetime.timedelta(days=1)
    
    print(f'Got {len(readings)} records')

    df = pd.DataFrame(readings, columns=['T', 'C', 'P'])
    df = df.set_index('T')

    bal = (0.8*df['P']-df['C']).cumsum()
    pl = bal.plot(x='T', figsize=(12,5))
    pl.text(0.4,0.9, f"Current balance: {bal[-1]:.1f} kWh", bbox=dict(facecolor='white', alpha=0.75), transform=pl.transAxes)
    pl.grid()
    pl.axhline(ls=':', lw=1)
    pl.get_figure().savefig('balance.pdf', bbox_inches='tight')

