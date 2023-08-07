#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from glob import glob
import numpy as np
import time
from datetime import timedelta
import datetime
import matplotlib.pyplot as plt 
import csv
figsize = (15,5)

CENTER=False
# Fix missing data causing the offset
CONS_OFF=2+11
PROD_OFF=14

readings = []
for fn in sorted(glob(f'data/*/*/*.csv')):
    with open(fn) as of:
        for t, c, p in csv.reader(of):
            readings.append([datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S"),float(c),float(p)])

print(f'Got {len(readings)} records')

df = pd.DataFrame(readings, columns=['T', 'Cons', 'Prod'])
df = df.set_index('T')


df['Eff. rate'] = 0.8*df['Prod']-df['Cons']
df['Bilans'] = df['Eff. rate'].cumsum()

#print(time.strftime('%Y-%m-%d'))

try :
    day = pd.read_csv(f"data/logger/{time.strftime('%Y-%m-%d')}_inverter-v5.csv", parse_dates=True, index_col='DateTime')
except  (pd.errors.EmptyDataError, FileNotFoundError) :
    day = None

#print(df.tail())
#print(day.tail())

# ==================================
# Daily Production/Consumption rates
# ==================================

span=3
#pl = df.ewm(span=24*30).mean().plot(figsize=(10,6));
pl = df.rolling(f'{span}d').mean().plot(y=['Prod', 'Cons'], figsize=figsize, lw=1);
er = 0.8*df['Prod']-df['Cons']
er.rolling(f'{span}d').mean().plot(ls='--', label='Effective rate')
er.rolling(f'30d', center=CENTER).mean().plot(ls='-', color='C2', label='Avg. Eff. rate')  
pl.grid()
pl.axhline(ls=':', color='k')
aprod=df['Prod'].mean()
#a1 = pl.axhline(aprod, ls=':')
a2 = pl.axhline(0.8*aprod, ls='--', label='avg. 0.8P')
a3 = pl.axhline(df['Cons'].mean(), ls='--', color='C1', label='avg. C')
pl.legend(loc='upper left')
pl.set_ylabel('Power (kW)')
pl.set_title(f'Avarage {span} day power rates,  [{df.index[-1].strftime("%Y/%m/%d %H:%M")}]');
pl.set_xlim(df.index[0], df.index[-1])
pl.get_figure().savefig("out/rates.png", bbox_inches='tight')

# =======================                                                                                                                               
# Year to Year production                                                                                                                               
# =======================                                                                                                                               

y2y = df['Bilans'].rolling('24h').mean()                                                                                                                
pl = (y2y-y2y.shift(periods=365, freq='D')).rolling('14d').mean().plot(y=['Bilans'], ls='-', label='One year', figure=plt.figure(figsize=figsize))
(y2y-y2y.shift(periods=2*365, freq='D')).rolling('14d').mean().plot(y=['Bilans'], ls='--', label='Two years')
pl.legend(loc='upper left')
pl.grid()
pl.axhline(ls=':', color='k')
pl.set_xlim(df.index[0], df.index[-1])
pl.set_ylabel('Balance (kWh)')
pl.set_title('Year-to-year balance')
pl.get_figure().savefig("out/y2y.png", bbox_inches='tight')                                                                                             

# ==============
# Energy balance
# ==============

#pl = (df.cumsum()/np.outer(1+np.arange(len(df)),np.ones(2))).ewm(span=24*7).mean().plot(figsize=(10,6));
#pl = (df.cumsum()/np.outer(1+np.arange(len(df)),np.ones(2))).rolling(24*7).mean().plot(figsize=figsize);
pl = df['Bilans'].rolling('24h').mean().plot.area(stacked=False, figure=plt.figure(figsize=figsize));

#(y2y-y2y.shift(periods=365, freq='D')).rolling('14d').mean().plot(y=['Bilans'], ls='-', label='One year')
#(y2y-y2y.shift(periods=2*365, freq='D')).rolling('14d').mean().plot(y=['Bilans'], ls='--', label='Two years')

pl.grid();
pl.axhline(0, ls='--', color='C2')
pl.text(0.4,0.9, f"Current balance: {df['Bilans'][-1]-CONS_OFF+0.8*PROD_OFF:.1f} kWh", bbox=dict(facecolor='white', alpha=0.75), transform=pl.transAxes)
pl.text(0.4,0.75, f"Prod: {df['Prod'].sum()+PROD_OFF:.0f} kWh\n"
		  f"Cons: {df['Cons'].sum()+CONS_OFF:.0f} kWh", bbox=dict(facecolor='white', alpha=0.75), transform=pl.transAxes)
pl.set_ylabel('Energy (kWh)');
pl.set_title(f'Energy balance,  [{df.index[-1].strftime("%Y/%m/%d %H:%M")}]');
pl.set_xlim(df.index[0], df.index[-1])
pl.set_ylim(None, None)
pl.get_figure().savefig("out/bilans.png", bbox_inches='tight')

# ==================================
# Last few days + current production
# ==================================

span = 4
ax = df[-24*(span+1):].plot(y=['Prod', 'Cons'], lw=1, figsize=figsize)
sht = df[-24*(span+1):]['Bilans'][0]
df[-24*(span+1):]['Eff. rate'].plot(lw=2)
((df[-24*(span+1):]['Bilans']-sht)/10).plot(lw=2)
ax.grid(which='both')
ax.set_ylabel('Power (kW) / Balance (kWh/10)')
ax.set_title(f'Hourly power (kW);  Last {span} days;  [{time.strftime("%Y/%m/%d %H:%M")}]');
ax.legend(loc='upper left')

xh = pd.to_datetime(time.strftime('%Y-%m-%d'))
xl = xh - timedelta(days=span)
xh = xh + timedelta(days=1)
#print(ax.get_xlim(), xl, xh)
ax.set_xlim(xl, xh)
#print(ax.get_xlim())

#ax.set_ylim(0,3.5)
#ax.axhline(df['Prod'].mean(), ls=':')
#ax.axhline(df['Prod'][-24*span:].mean(), ls='--')
#ax.axhline(df['Cons'].mean(), ls=':', color='C1')
#ax.axhline(df['Cons'][-24*span:].mean(), ls='--', color='C1')
ax_pos = ax.get_position()

ax2 = ax.inset_axes((span/(span+1),0,1/(span+1),1))

ax2.set_ylim(0,3.5)
ax2.yaxis.tick_right()

if day is not None :
    day['AC_AP'].plot(ax=ax2, ls='-', lw=0, color='C0', label='Power', marker='.', ms=2)
    day['AC_AP'].rolling('600s', center=CENTER).mean().plot.area(ax=ax2, color='C6', alpha=0.5, lw=1, label='10m avg')

    xl, xh = ax2.get_xlim()
    ax2.set_xlim(int(xl),int(xl)+1)
    xl, xh = ax2.get_xlim()



    ax2.text(0.05,0.8, f"E ={day['E_TODAY'][-1]:.2f} kWh\n"
                   f"P_={day['E_TODAY'][-1]/24:.3f} kW\n"
                   f"P ={day['AC_AP'][-1]:.2f} kW", 
                   bbox=dict(facecolor='white', alpha=0.75),
                   transform=ax2.transAxes)

    day['AC_AP'][-1:].plot(ax=ax2, lw=0, color='C3', marker='.', ms=4)

    hours = [3, 6, 9, 12, 15, 18, 21]
    ax2.set_xticks([int(xl)+h/24 for h in hours[1::2]])
    ax2.set_xticklabels(hours[1::2])
    for h in hours:
        ax2.axvline(int(xl)+h/24, ls='--' if h in [6, 12, 18] else ':', lw=1)

    ax2.grid(ls=":", lw=1)
    ax2.set_xlabel('Time')


    #ax2.patch.set_alpha(0.85)
#print(day[-10:])
#print(df[-10:])
#dt = (day.index[1:]-day.index[:-1])
#mprod = day['E_TODAY'].rolling(5,center=True).mean()
#dt = (mprod.index[1:]-mprod.index[:-1])
#(mprod.diff()[1:]/((day.index[1:]-day.index[:-1]).total_seconds()/3600)).plot(ax=ax2, ls='--', color='C1')
#day['E_TODAY'].plot(ax=ax2, ls='--', color='C1')
#ax2.set_ylim(0, 20)
#(day['E_TODAY'].diff()[1:]/((day.index[1:]-day.index[:-1]).total_seconds()/3600)).plot();
#pd.DataFrame(np.array(day['E_TODAY'].rolling(5,center=True).mean().diff()[1:]/(dt.total_seconds()/3600)), 
#             index=day.index[:-1]+dt/2).rolling(10, center=True).mean().plot(ax=ax2, ls='-', lw=1, color='C1')

ax.legend(loc='upper left');

#print(ax.get_xlim())

ax.get_figure().savefig("out/recent.png", bbox_inches='tight')


