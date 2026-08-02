import datetime
import pandas as pd
import csv
from glob import glob

readings = []
for fn in sorted(glob(f'data/*/*/*.csv')):
    with open(fn) as of:
        for t, c, p in csv.reader(of):
            readings.append([datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S"),float(c),float(p)])

print(f'Got {len(readings)} records')

df = pd.DataFrame(readings, columns=['T', 'C', 'P'])
df = df.set_index('T')

bal = (0.8*df['P']-df['C']).cumsum()
pl = bal.plot(x='T', figsize=(12,5))
pl.text(0.4,0.9, f"Current balance: {bal[-1]:.1f} kWh", bbox=dict(facecolor='white', alpha=0.75), transform=pl.transAxes)
pl.grid()
pl.axhline(ls=':', lw=1)
pl.get_figure().savefig('balance.pdf', bbox_inches='tight')
