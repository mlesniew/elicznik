# Tauron eLicznik Scraper

This Python 3 package allows to read electric energy meter reading history from the 
[Tauron eLicznik](https://elicznik.tauron-dystrybucja.pl/) website.


## Installation

The package can be installed using pip:

```
$ pip3 install elicznik
```

or alternatively:
```
$ pip3 install git@github.com:mlesniew/elicznik.git
```



## Command line usage

With the package installed readings can be retrieved by simply running the `elicznik` command:
```
usage: elicznik [-h] [--format {table,csv}] [--api {chart,csv}] [--site SITE] username password [start_date] [end_date]

positional arguments:
  username              tauron-dystrybucja.pl user name
  password              tauron-dystrybucja.pl password
  start_date            Start date of date range to be retrieved, in ISO8601 format. If the end date is omitted, it's the only date for which measurements are retrieved.
  end_date              End date of date range to be retrieved, inclusive, in ISO8601 format. Can be omitted to only retrieve a single day's measurements.

options:
  -h, --help            show this help message and exit
  --format {table,csv}  Specify the output format
  --api {chart,csv}     Specify which Tauron API to use to get the measurements
  --site SITE           site identifier, must match '[0-9]+_[0-9]+_[0-9]+'
(venv) ~/src/elicznik (site) $ elicznik --help | cat
usage: elicznik [-h] [--format {table,csv}] [--api {chart,csv}] [--site SITE]
                username password [start_date] [end_date]

positional arguments:
  username              tauron-dystrybucja.pl user name
  password              tauron-dystrybucja.pl password
  start_date            Start date of date range to be retrieved, in ISO8601
                        format. If the end date is omitted, it's the only date
                        for which measurements are retrieved.
  end_date              End date of date range to be retrieved, inclusive, in
                        ISO8601 format. Can be omitted to only retrieve a
                        single day's measurements.

options:
  -h, --help            show this help message and exit
  --format {table,csv}  Specify the output format
  --api {chart,csv}     Specify which Tauron API to use to get the
                        measurements
  --site SITE           site identifier, must match '[0-9]+_[0-9]+_[0-9]+'
```


### Example

```
$ elicznik freddy@example.com secretpassword 2022-07-20
timestamp              consumed    produced    net consumption    net production
-------------------  ----------  ----------  -----------------  ----------------
2022-07-20 00:00:00       0.133       0                  0.133             0
2022-07-20 01:00:00       0.127       0                  0.127             0
2022-07-20 02:00:00       0.119       0                  0.119             0
2022-07-20 03:00:00       0.119       0                  0.119             0
2022-07-20 04:00:00       0.124       0                  0.124             0
2022-07-20 05:00:00       0.02        0.226              0                 0.206
2022-07-20 06:00:00       0           1.058              0                 1.058
2022-07-20 07:00:00       0.086       1.607              0                 1.521
2022-07-20 08:00:00       0           2.09               0                 2.09
2022-07-20 09:00:00       0           2.302              0                 2.302
2022-07-20 10:00:00       0.223       2.427              0                 2.204
2022-07-20 11:00:00       0.031       2.723              0                 2.692
2022-07-20 12:00:00       0           2.818              0                 2.818
2022-07-20 13:00:00       0           2.735              0                 2.735
2022-07-20 14:00:00       0           2.413              0                 2.413
2022-07-20 15:00:00       0           1.953              0                 1.953
2022-07-20 16:00:00       0.316       1.407              0                 1.091
2022-07-20 17:00:00       0.183       1.2                0                 1.017
2022-07-20 18:00:00       0.001       0.843              0                 0.842
2022-07-20 19:00:00       0.446       0.274              0.172             0
2022-07-20 20:00:00       0.712       0                  0.712             0
2022-07-20 21:00:00       0.225       0                  0.225             0
2022-07-20 22:00:00       0.207       0                  0.207             0
2022-07-20 23:00:00       0.15        0                  0.15              0
```


## API usage

```
import datetime
import elicznik

with elicznik.ELicznik("freddy@example.com", "secretpassword", "optional_site_identifier") as m:
    # date range
    print("July 2021")

    readings = m.get_readings(datetime.date(2021, 7, 1), datetime.date(2021, 7, 31))

    for timestamp, consumed, produced, consumed_net, produced_net in readings:
        print(timestamp, consumed, produced, consumed_net, produced_net)

    # single day
    print("Yesterday")

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    readings = m.get_readings(yesterday)

    for timestamp, consumed, produced, consumed_net, produced_net in readings:
        print(timestamp, consumed, produced, consumed_net, produced_net)
```


## Notes on APIs and the `--api` command line switch

Tauron exposes two API endpoints for retrieving meter readings -- one for downloading CSV (and XLS) data,
the other is a back-end supporting the charts in the Web UI.  In theory, both endpoints are equivalent.
They can be used to get exactly the same data.  In practice, the endpoint for downloading CSV data seems
more stable -- in contrast to the chart one, which changed a few times in the past.  The CSV endpoint is
also more robust and allows downloading more data with fewer requests.

This project supports fetching data from both.  CSV is the default and recommended one, but it's possible
to switch to the chart API endpoint in case of problems.

This can be done by adding `--api=chart` on the command line:
```
$ elicznik --api=chart freddy@example.com secretpassword 2021-07-10
```

Both APIs can also be used explicitly from code.  The `elicznik` module defines two classes for that `ELicznikChart`
and `ELicznikCSV`.  `ELicznik` is just an alias for `ELicznikCSV`:
```
import elicznik

with elicznik.ELicznikChart("freddy@example.com", "secretpassword") as m:
    ...
```


## TODO & bugs

* Convert the dates to UTC and handle switches from and to DST properly
* Make the dependency on tabulate optional


## Similar projects

This project is based on the excellent
[tauron-elicznik-scrapper](https://github.com/MichalZaniewicz/tauron-elicznik-scraper) project by
[Michał Zaniewicz](https://github.com/MichalZaniewicz), but there are several other available out there.

Among the other [similar eLicznik projects on GitHub](https://github.com/search?q=elicznik) there's one especially
worth checking out:
the [Tauron AMIplus sensor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Tauron-AMIplus) -- it's
an eLicznik Home Assistant integration.
